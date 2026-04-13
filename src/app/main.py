"""
FastAPI メインエントリポイント
API仕様: docs/spec/03_api_spec.md
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse

from app.models.request import ProcessOptions
from app.models.response import (
    JobCreated, JobStatus, JobResult, ResultFiles,
    StepStatus, HealthResponse,
)
from app.pipeline.extractor import Extractor
from app.pipeline.summarizer import Summarizer
from app.pipeline.transcriber import Transcriber
from app.utils.file_handler import (
    load_settings, generate_job_id, create_job_dirs,
    delete_upload, delete_temp, zip_output,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = load_settings()

app = FastAPI(title="Media Transcriber API")

# ジョブ状態をメモリ管理（シングルインスタンム用）
_jobs: dict[str, dict] = {}


@app.get("/api/health", response_model=HealthResponse)
async def health():
    ollama_status = "disconnected"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{settings['ollama']['base_url']}/api/tags",
                timeout=3,
            )
            if r.status_code == 200:
                ollama_status = "connected"
    except Exception:
        pass
    return HealthResponse(
        status="ok",
        ollama=ollama_status,
        whisper_model=settings["whisper"]["model"],
    )


@app.post("/api/upload", response_model=JobCreated)
async def upload(
    file: UploadFile = File(...),
    language: str = Form("ja"),
    mode: str = Form("full"),
):
    job_id = generate_job_id()
    job_dirs = create_job_dirs(job_id, settings)

    # ファイル保存
    upload_path = job_dirs["upload"] / file.filename
    content = await file.read()
    upload_path.write_bytes(content)

    _jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "current_step": None,
        "steps": StepStatus().model_dump(),
        "error": None,
        "filename": file.filename,
        "upload_path": str(upload_path),
        "job_dirs": {k: str(v) for k, v in job_dirs.items()},
        "language": language,
        "mode": mode,
        "created_at": datetime.now().isoformat(),
    }

    # バックグラウンドで処理開始
    asyncio.create_task(_run_pipeline(job_id))

    return JobCreated(
        job_id=job_id,
        status="queued",
        filename=file.filename,
        created_at=datetime.now(),
    )


@app.get("/api/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    job = _get_job(job_id)
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        current_step=job["current_step"],
        steps=StepStatus(**job["steps"]),
        error=job.get("error"),
    )


@app.get("/api/result/{job_id}", response_model=JobResult)
async def get_result(job_id: str):
    job = _get_job(job_id)
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="処理が完了していません")

    output_dir = Path(job["job_dirs"]["output"])
    slides_dir = output_dir / "slides"

    files = ResultFiles(
        transcript   = _rel(output_dir / "transcript.txt"),
        slides       = [_rel(p) for p in sorted(slides_dir.glob("*.png"))] if slides_dir.exists() else [],
        slides_text  = _rel(output_dir / "slides_text.txt"),
        summary      = _rel(output_dir / "summary.md"),
        minutes      = _rel(output_dir / "minutes.md"),
    )
    return JobResult(job_id=job_id, status="completed", files=files)


@app.get("/api/download/{job_id}")
async def download(job_id: str):
    job = _get_job(job_id)
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="処理が完了していません")

    zip_path = zip_output(job_id, settings)
    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=f"{job_id}_result.zip",
    )


@app.delete("/api/job/{job_id}")
async def delete_job(job_id: str):
    _get_job(job_id)
    delete_upload(job_id, settings)
    delete_temp(job_id, settings)
    _jobs.pop(job_id, None)
    return {"job_id": job_id, "deleted": True}


# --- 内部処理 ---

def _get_job(job_id: str) -> dict:
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="ジョブが見つかりません")
    return _jobs[job_id]


def _rel(path: Path) -> str | None:
    return str(path) if path.exists() else None


def _update(job_id: str, step: str, progress: int, step_status: str):
    _jobs[job_id]["current_step"] = step
    _jobs[job_id]["progress"] = progress
    _jobs[job_id]["steps"][step] = step_status
    _jobs[job_id]["status"] = "processing"


async def _run_pipeline(job_id: str):
    job = _jobs[job_id]
    job_dirs = {k: Path(v) for k, v in job["job_dirs"].items()}
    input_path = Path(job["upload_path"])
    mode = job["mode"]
    language = job["language"]

    try:
        suffix = input_path.suffix.lower()
        is_video = suffix in {".mp4", ".mkv", ".avi", ".mov"}

        # ステップ1: 文字起こし
        if mode in ("transcribe_only", "full"):
            _update(job_id, "transcribing", 10, "in_progress")
            transcriber = await asyncio.get_event_loop().run_in_executor(
                None, Transcriber, settings
            )
            await asyncio.get_event_loop().run_in_executor(
                None, transcriber.run, input_path, job_dirs, language
            )
            _jobs[job_id]["steps"]["transcribing"] = "completed"
            _jobs[job_id]["progress"] = 40
        else:
            _jobs[job_id]["steps"]["transcribing"] = "skipped"

        # ステップ2: スライド抽出（動画のみ）
        if mode in ("extract_only", "full") and is_video:
            _update(job_id, "extracting", 50, "in_progress")
            extractor = await asyncio.get_event_loop().run_in_executor(
                None, Extractor, settings
            )
            await asyncio.get_event_loop().run_in_executor(
                None, extractor.run, input_path, job_dirs
            )
            _jobs[job_id]["steps"]["extracting"] = "completed"
            _jobs[job_id]["progress"] = 70
        else:
            _jobs[job_id]["steps"]["extracting"] = "skipped"

        # ステップ3: 要約・議事録
        if mode == "full":
            _update(job_id, "summarizing", 75, "in_progress")
            summarizer = await asyncio.get_event_loop().run_in_executor(
                None, Summarizer, settings
            )
            await asyncio.get_event_loop().run_in_executor(
                None, summarizer.run, job_dirs
            )
            _jobs[job_id]["steps"]["summarizing"] = "completed"
            _jobs[job_id]["steps"]["minutes"] = "completed"
            _jobs[job_id]["progress"] = 100

        # 正常完了 → アップロードファイル削除
        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["progress"] = 100
        if settings["storage"]["delete_upload_on_success"]:
            delete_upload(job_id, settings)
            logger.info(f"アップロードファイル削除完了: {job_id}")

    except Exception as e:
        logger.error(f"処理エラー [{job_id}]: {e}")
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)
    finally:
        delete_temp(job_id, settings)


if __name__ == "__main__":
    import threading
    from app.ui.gradio_app import demo

    def run_gradio():
        demo.launch(server_name="0.0.0.0", server_port=7860, prevent_thread_lock=True)

    t = threading.Thread(target=run_gradio, daemon=True)
    t.start()

    uvicorn.run(
        "app.main:app",
        host=settings["server"]["host"],
        port=settings["server"]["port"],
        reload=False,
    )
