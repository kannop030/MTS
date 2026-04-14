import logging
import sys
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def _cleanup_old_logs(log_dir: Path, log_file: str, retention_days: int) -> None:
    """retention_days より古いローテーション済みログファイルを削除する。"""
    cutoff = datetime.now() - timedelta(days=retention_days)
    stem = Path(log_file).stem
    suffix = Path(log_file).suffix
    deleted = 0
    for f in log_dir.iterdir():
        if not f.is_file():
            continue
        # TimedRotatingFileHandler が生成するファイル名: carol.log.2026-01-01
        name = f.name
        if not (name.startswith(stem) and name != log_file):
            continue
        # 末尾の日付部分を取得
        date_part = name[len(stem + suffix) + 1:] if suffix else name[len(stem) + 1:]
        try:
            file_date = datetime.strptime(date_part, "%Y-%m-%d")
        except ValueError:
            continue
        if file_date < cutoff:
            f.unlink()
            deleted += 1
    if deleted:
        logging.getLogger(__name__).info(
            f"古いログファイルを {deleted} 件削除しました（{retention_days} 日以前）"
        )


def setup_file_logging(log_dir: str, log_file: str, log_level: str, retention_days: int) -> None:
    """アプリ起動時に一度だけ呼び出してファイルログを設定する。"""
    dir_path = Path(log_dir)
    dir_path.mkdir(parents=True, exist_ok=True)

    log_path = dir_path / log_file
    level = getattr(logging, log_level.upper(), logging.INFO)

    root = logging.getLogger()
    # 既にファイルハンドラが設定済みならスキップ
    if any(isinstance(h, TimedRotatingFileHandler) for h in root.handlers):
        return

    file_handler = TimedRotatingFileHandler(
        filename=str(log_path),
        when="midnight",
        interval=1,
        backupCount=0,       # backupCount=0 でも rotate 自体は行われる
        encoding="utf-8",
        utc=False,
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    file_handler.setLevel(level)
    root.addHandler(file_handler)

    # 古いログを削除
    _cleanup_old_logs(dir_path, log_file, retention_days)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers and not logging.getLogger().handlers:
        stream = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1, closefd=False)
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
