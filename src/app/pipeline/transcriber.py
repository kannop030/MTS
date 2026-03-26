"""
Transcriber: 動画・音声ファイルから文字起こしを行う
仕様: docs/design/transcriber.md
"""
from pathlib import Path

import ffmpeg
from faster_whisper import WhisperModel

from app.utils.logger import get_logger

logger = get_logger(__name__)

SUPPORTED_VIDEO = {".mp4", ".mkv", ".avi", ".mov"}
SUPPORTED_AUDIO = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}


class Transcriber:
    def __init__(self, settings: dict):
        cfg = settings["whisper"]
        logger.info(f"Whisperモデル読み込み中: {cfg['model']}")
        self.model = WhisperModel(
            cfg["model"],
            device=cfg["device"],
            compute_type=cfg["compute_type"],
        )
        self.language = cfg["language"]

    def extract_audio(self, input_path: Path, output_path: Path) -> Path:
        logger.info(f"音声抽出: {input_path.name}")
        (
            ffmpeg
            .input(str(input_path))
            .output(str(output_path), ar=16000, ac=1, f="wav")
            .overwrite_output()
            .run(quiet=True)
        )
        return output_path

    def transcribe(self, audio_path: Path) -> list:
        logger.info("文字起こし開始")
        segments, _ = self.model.transcribe(
            str(audio_path),
            language=self.language,
        )
        return list(segments)

    def save(self, segments: list, output_path: Path) -> None:
        lines = []
        for seg in segments:
            start = _fmt_time(seg.start)
            end = _fmt_time(seg.end)
            lines.append(f"[{start} --> {end}] {seg.text.strip()}")
        output_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"文字起こし保存: {output_path}")

    def run(self, input_path: Path, job_dirs: dict, language: str = None) -> Path:
        if language:
            self.language = language

        suffix = input_path.suffix.lower()
        if suffix in SUPPORTED_VIDEO:
            audio_path = job_dirs["temp"] / "audio.wav"
            self.extract_audio(input_path, audio_path)
        elif suffix in SUPPORTED_AUDIO:
            audio_path = input_path
        else:
            raise ValueError(f"非対応のファイル形式: {suffix}")

        segments = self.transcribe(audio_path)
        output_path = job_dirs["output"] / "transcript.txt"
        self.save(segments, output_path)
        return output_path


def _fmt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"
