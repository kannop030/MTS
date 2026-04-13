"""
フォルダ監視モジュール: 指定フォルダを監視して自動でパイプライン処理を実行する
"""
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from app.pipeline.extractor import Extractor
from app.pipeline.summarizer import Summarizer
from app.pipeline.transcriber import Transcriber
from app.utils.file_handler import (
    create_job_dirs,
    delete_temp,
    generate_job_id,
    load_settings,
    sanitize_filename,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov",  # 動画
    ".mp3", ".wav", ".m4a", ".ogg", ".flac",  # 音声
}

# ファイル書き込み完了を確認する待機時間（秒）
_STABLE_WAIT = 2.0
_STABLE_CHECKS = 3


def _wait_for_stable(path: Path) -> bool:
    """ファイルの書き込みが完了するまで待つ。安定したらTrueを返す。"""
    prev_size = -1
    for _ in range(_STABLE_CHECKS):
        time.sleep(_STABLE_WAIT)
        try:
            size = path.stat().st_size
        except OSError:
            return False
        if size == prev_size and size > 0:
            return True
        prev_size = size
    return False


class _MediaEventHandler(FileSystemEventHandler):
    def __init__(self, watcher: "FolderWatcher"):
        super().__init__()
        self._watcher = watcher
        self._seen: set[str] = set()

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return
        key = str(path.resolve())
        if key in self._seen:
            return
        self._seen.add(key)
        self._watcher.process_file(path)

    def on_moved(self, event):
        """別ディレクトリからの移動（mv）にも対応する。"""
        if event.is_directory:
            return
        path = Path(event.dest_path)
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return
        key = str(path.resolve())
        if key in self._seen:
            return
        self._seen.add(key)
        self._watcher.process_file(path)


class FolderWatcher:
    """
    watch_dir を監視し、対応ファイルを自動でパイプライン処理する。

    処理結果は output_dir/{job_id}/ に保存される。
    正常完了したファイルは削除される。
    失敗したファイルは failed_dir/ へ移動される。
    """

    def __init__(self, settings: dict | None = None):
        self.settings = settings or load_settings()
        cfg = self.settings.get("watcher", {})

        self.watch_dir = Path(cfg.get("watch_dir", "data/watch"))
        self.language = cfg.get("language", self.settings["whisper"].get("language", "ja"))
        self.enable_ocr = cfg.get("enable_ocr", False)
        self.enable_minutes = cfg.get("enable_minutes", False)

        self.failed_dir = self.watch_dir / "failed"

        for d in (self.watch_dir, self.failed_dir):
            d.mkdir(parents=True, exist_ok=True)

        logger.info(f"監視フォルダ: {self.watch_dir.resolve()}")
        logger.info(
            f"設定 — 言語: {self.language}, OCR: {self.enable_ocr}, 議事録: {self.enable_minutes}"
        )

    # ------------------------------------------------------------------
    # パイプライン実行
    # ------------------------------------------------------------------

    def process_file(self, input_path: Path) -> None:
        logger.info(f"ファイル検知: {input_path.name}")

        if not _wait_for_stable(input_path):
            logger.warning(f"ファイルが安定しないためスキップ: {input_path.name}")
            return

        job_id = generate_job_id()
        filename_stem = sanitize_filename(input_path.name)
        job_dirs = create_job_dirs(job_id, self.settings)
        suffix = input_path.suffix.lower()
        is_video = suffix in {".mp4", ".mkv", ".avi", ".mov"}

        logger.info(f"処理開始 [{job_id}]: {input_path.name}")

        try:
            # ステップ1: 文字起こし
            logger.info(f"[{job_id}] 文字起こし中...")
            transcriber = Transcriber(self.settings)
            transcriber.run(input_path, job_dirs, self.language, filename_stem)

            # ステップ2: スライド抽出（動画かつOCR有効の場合のみ）
            if self.enable_ocr and is_video:
                logger.info(f"[{job_id}] スライド抽出中...")
                extractor = Extractor(self.settings)
                extractor.run(input_path, job_dirs, filename_stem)

            # ステップ3: 要約・議事録（有効な場合のみ）
            if self.enable_minutes:
                logger.info(f"[{job_id}] 要約・議事録生成中...")
                summarizer = Summarizer(self.settings)
                summarizer.run(job_dirs, filename_stem)

            output_dir = Path(self.settings["storage"]["output_dir"]) / job_id
            logger.info(f"[{job_id}] 処理完了 → {output_dir.resolve()}")

            # 元ファイルを削除
            input_path.unlink()
            logger.info(f"[{job_id}] ファイルを削除: {input_path.name}")

        except Exception as exc:
            logger.error(f"[{job_id}] 処理失敗: {exc}")
            dest = self.failed_dir / input_path.name
            _move_unique(input_path, dest)
            logger.info(f"[{job_id}] ファイルを failed/ へ移動: {dest.name}")

        finally:
            delete_temp(job_id, self.settings)

    # ------------------------------------------------------------------
    # 監視開始
    # ------------------------------------------------------------------

    def run_forever(self) -> None:
        """フォルダ監視を開始し、Ctrl+C で停止するまでブロックする。"""
        # 既存ファイルを先に処理
        self._process_existing()

        handler = _MediaEventHandler(self)
        observer = Observer()
        observer.schedule(handler, str(self.watch_dir), recursive=False)
        observer.start()
        logger.info("監視開始（停止: Ctrl+C）")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            observer.stop()
            observer.join()
            logger.info("監視停止")

    def _process_existing(self) -> None:
        """起動時に watch_dir に残っているファイルを処理する。"""
        files = [
            p for p in self.watch_dir.iterdir()
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        if files:
            logger.info(f"既存ファイル {len(files)} 件を処理します")
            for f in files:
                self.process_file(f)


# ------------------------------------------------------------------
# ヘルパー
# ------------------------------------------------------------------

def _move_unique(src: Path, dest: Path) -> Path:
    """同名ファイルが存在する場合は連番を付けて移動する。"""
    if not dest.exists():
        src.rename(dest)
        return dest
    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    i = 1
    while True:
        candidate = parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            src.rename(candidate)
            return candidate
        i += 1
