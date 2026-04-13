"""
Gradio Web UI
"""
import time
from pathlib import Path

import gradio as gr
import httpx

API_BASE = "http://127.0.0.1:8000"


def process_file(file_obj, language: str, enable_ocr: bool, enable_minutes: bool) -> tuple:
    if file_obj is None:
        return "ファイルを選択してください", None, None, None, None, None

    filename = Path(file_obj.name).name

    # アップロード
    with open(file_obj.name, "rb") as f:
        resp = httpx.post(
            f"{API_BASE}/api/upload",
            files={"file": (filename, f)},
            data={
                "language": language,
                "enable_ocr": str(enable_ocr).lower(),
                "enable_minutes": str(enable_minutes).lower(),
            },
            timeout=120,
        )

    if resp.status_code != 200:
        return f"エラー: {resp.text}", None, None, None, None, None

    job_id = resp.json()["job_id"]

    # 処理完了まで待機（最大6時間）
    status = "processing"
    for _ in range(7200):
        time.sleep(3)
        status_resp = httpx.get(f"{API_BASE}/api/status/{job_id}", timeout=10)
        data = status_resp.json()
        status = data["status"]
        progress = data["progress"]
        step = data.get("current_step") or ""

        yield f"処理中... {progress}% ({step})", None, None, None, None, None

        if status == "completed":
            break
        if status == "failed":
            yield f"エラー: {data.get('error', '不明なエラー')}", None, None, None, None, None
            return

    if status != "completed":
        yield "タイムアウト: 処理が完了しませんでした", None, None, None, None, None
        return

    # 結果取得
    result_resp = httpx.get(f"{API_BASE}/api/result/{job_id}", timeout=10)
    files = result_resp.json()["files"]

    def read_file(path):
        if path and Path(path).exists():
            return Path(path).read_text(encoding="utf-8")
        return ""

    transcript  = read_file(files.get("transcript"))
    slides_text = read_file(files.get("slides_text"))
    summary     = read_file(files.get("summary"))
    minutes     = read_file(files.get("minutes"))

    # ZIPダウンロードリンク
    zip_url = f"{API_BASE}/api/download/{job_id}"

    yield "処理完了", transcript, slides_text, summary, minutes, zip_url


with gr.Blocks(title="Media Transcriber") as demo:
    gr.Markdown("# Media Transcriber & Summarizer")
    gr.Markdown("動画・音声ファイルから文字起こし・スライド抽出・要約・議事録を生成します。")

    with gr.Row():
        with gr.Column(scale=1):
            file_input = gr.File(
                label="ファイルを選択（動画/音声）",
                file_types=[".mp4", ".mkv", ".avi", ".mov", ".mp3", ".wav", ".m4a", ".ogg", ".flac"],
            )
            language = gr.Dropdown(
                choices=["ja", "en", "auto"],
                value="ja",
                label="言語",
            )
            gr.Markdown("**処理オプション**（文字起こしは常に実行されます）")
            enable_ocr = gr.Checkbox(
                label="OCR（スライド抽出）を実行する",
                value=False,
            )
            enable_minutes = gr.Checkbox(
                label="要約・議事録を生成する",
                value=False,
            )
            run_btn = gr.Button("処理開始", variant="primary")
            status_box = gr.Textbox(label="ステータス", interactive=False)

        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.Tab("文字起こし"):
                    transcript_out = gr.Textbox(label="文字起こし結果", lines=15, interactive=False)
                with gr.Tab("スライドテキスト"):
                    slides_out = gr.Textbox(label="スライドOCR結果", lines=15, interactive=False)
                with gr.Tab("要約"):
                    summary_out = gr.Markdown(label="要約")
                with gr.Tab("議事録"):
                    minutes_out = gr.Markdown(label="議事録")

    download_link = gr.Textbox(label="ZIPダウンロードURL", interactive=False)

    run_btn.click(
        fn=process_file,
        inputs=[file_input, language, enable_ocr, enable_minutes],
        outputs=[status_box, transcript_out, slides_out, summary_out, minutes_out, download_link],
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
