import re
import shutil
import uuid
from pathlib import Path

import yaml


def sanitize_filename(filename: str) -> str:
    """ファイル名をサニタイズして安全なファイル名にする（日本語対応）。
    拡張子を除いたstemを返す。日本語文字はそのまま保持する。
    """
    stem = Path(filename).stem
    # パスで使用できない文字を _ に置換（日本語・Unicode文字は保持）
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', stem)
    # 先頭・末尾のスペースとドットを除去
    stem = stem.strip('. ')
    return stem if stem else 'output'


def load_settings(config_path: str = "config/settings.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def generate_job_id() -> str:
    return str(uuid.uuid4())


def create_job_dirs(job_id: str, settings: dict) -> dict[str, Path]:
    dirs = {
        "upload": Path(settings["storage"]["upload_dir"]) / job_id,
        "output": Path(settings["storage"]["output_dir"]) / job_id,
        "slides": Path(settings["storage"]["output_dir"]) / job_id / "slides",
        "temp":   Path(settings["storage"]["temp_dir"]) / job_id,
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def delete_upload(job_id: str, settings: dict) -> None:
    upload_dir = Path(settings["storage"]["upload_dir"]) / job_id
    if upload_dir.exists():
        shutil.rmtree(upload_dir)


def delete_temp(job_id: str, settings: dict) -> None:
    temp_dir = Path(settings["storage"]["temp_dir"]) / job_id
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


def zip_output(job_id: str, settings: dict, filename_stem: str = "") -> Path:
    output_dir = Path(settings["storage"]["output_dir"]) / job_id
    base_name = f"{filename_stem}_result" if filename_stem else f"{job_id}_result"
    zip_path = Path(settings["storage"]["output_dir"]) / base_name
    shutil.make_archive(str(zip_path), "zip", str(output_dir))
    return Path(str(zip_path) + ".zip")
