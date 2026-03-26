import shutil
import uuid
from pathlib import Path

import yaml


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


def zip_output(job_id: str, settings: dict) -> Path:
    output_dir = Path(settings["storage"]["output_dir"]) / job_id
    zip_path = Path(settings["storage"]["output_dir"]) / f"{job_id}_result"
    shutil.make_archive(str(zip_path), "zip", str(output_dir))
    return Path(str(zip_path) + ".zip")
