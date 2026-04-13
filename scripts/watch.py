#!/usr/bin/env python3
"""
フォルダ監視モード起動スクリプト

使い方:
    python scripts/watch.py [--config config/settings.yaml]
    python scripts/watch.py --language en --ocr --minutes

media ファイルを data/watch/ に置くと自動でパイプライン処理を実行し、
結果を data/outputs/<job_id>/ に保存します。
"""
import argparse
import sys
from pathlib import Path

# プロジェクトルートを sys.path に追加
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.utils.file_handler import load_settings
from app.utils.logger import get_logger
from app.watcher import FolderWatcher

logger = get_logger("watch")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="指定フォルダを監視して自動でメディアを処理します"
    )
    parser.add_argument(
        "--config",
        default="config/settings.yaml",
        help="設定ファイルのパス (default: config/settings.yaml)",
    )
    parser.add_argument(
        "--watch-dir",
        default=None,
        help="監視フォルダのパス (default: settings.yaml の watcher.watch_dir)",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="文字起こし言語 (ja/en/auto, default: settings.yaml の値)",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        default=None,
        help="スライドOCRを有効にする",
    )
    parser.add_argument(
        "--minutes",
        action="store_true",
        default=None,
        help="要約・議事録生成を有効にする",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings(args.config)

    # CLI 引数で settings を上書き
    watcher_cfg = settings.setdefault("watcher", {})
    if args.watch_dir is not None:
        watcher_cfg["watch_dir"] = args.watch_dir
    if args.language is not None:
        watcher_cfg["language"] = args.language
    if args.ocr:
        watcher_cfg["enable_ocr"] = True
    if args.minutes:
        watcher_cfg["enable_minutes"] = True

    watcher = FolderWatcher(settings)
    watcher.run_forever()


if __name__ == "__main__":
    main()
