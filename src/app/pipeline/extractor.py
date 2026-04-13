"""
Extractor: 動画からスライド画像とOCRテキストを抽出する
仕様: docs/design/extractor.md
"""
from pathlib import Path

import cv2
import easyocr
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector

from app.utils.logger import get_logger

logger = get_logger(__name__)


class Extractor:
    def __init__(self, settings: dict):
        cfg_scene = settings["scene_detect"]
        cfg_ocr = settings["ocr"]
        self.threshold = cfg_scene["threshold"]
        self.min_scene_len = cfg_scene["min_scene_len"]
        logger.info("EasyOCR初期化中")
        self.reader = easyocr.Reader(
            cfg_ocr["languages"],
            gpu=cfg_ocr["gpu"],
        )

    def detect_scenes(self, video_path: Path) -> list[int]:
        logger.info("シーン検出中")
        video = open_video(str(video_path))
        scene_manager = SceneManager()
        scene_manager.add_detector(
            ContentDetector(
                threshold=self.threshold,
                min_scene_len=self.min_scene_len,
            )
        )
        scene_manager.detect_scenes(video)
        scenes = scene_manager.get_scene_list()
        frame_numbers = [s[0].get_frames() for s in scenes]
        logger.info(f"シーン検出数: {len(frame_numbers)}")
        return frame_numbers

    def extract_slides(self, video_path: Path, frame_numbers: list[int], output_dir: Path) -> list[Path]:
        cap = cv2.VideoCapture(str(video_path))
        saved = []
        for i, fn in enumerate(frame_numbers):
            cap.set(cv2.CAP_PROP_POS_FRAMES, fn)
            ret, frame = cap.read()
            if not ret:
                continue
            out_path = output_dir / f"slide_{i+1:03d}.png"
            cv2.imwrite(str(out_path), frame)
            saved.append(out_path)
        cap.release()
        logger.info(f"スライド画像保存: {len(saved)}枚")
        return saved

    def run_ocr(self, image_paths: list[Path]) -> dict[str, str]:
        results = {}
        for path in image_paths:
            logger.info(f"OCR処理: {path.name}")
            detections = self.reader.readtext(str(path), detail=0)
            results[path.name] = "\n".join(detections)
        return results

    def save_slides_text(self, ocr_results: dict[str, str], output_path: Path) -> None:
        lines = []
        for filename, text in ocr_results.items():
            lines.append(f"--- {filename} ---")
            lines.append(text)
            lines.append("")
        output_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"スライドテキスト保存: {output_path}")

    def run(self, video_path: Path, job_dirs: dict, filename_stem: str = "") -> tuple[list[Path], Path]:
        frame_numbers = self.detect_scenes(video_path)

        if not frame_numbers:
            logger.warning("シーンが検出されませんでした。先頭フレームのみ抽出します。")
            frame_numbers = [0]

        slides = self.extract_slides(video_path, frame_numbers, job_dirs["slides"])
        ocr_results = self.run_ocr(slides)

        name = f"{filename_stem}_slides_text.txt" if filename_stem else "slides_text.txt"
        text_path = job_dirs["output"] / name
        self.save_slides_text(ocr_results, text_path)

        return slides, text_path
