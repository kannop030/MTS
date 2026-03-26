# 詳細設計: Extractor（スライド抽出）

## 責務
動画からシーン変化を検出し、スライド画像とOCRテキストを抽出する。

## クラス設計

```python
class Extractor:
    def extract_frames(self, video_path: str, output_dir: str) -> list[str]
    def detect_scenes(self, video_path: str) -> list[int]
    def save_slides(self, frame_paths: list[str], scene_frames: list[int], output_dir: str) -> list[str]
    def run_ocr(self, image_paths: list[str]) -> dict[str, str]
    def save_slides_text(self, ocr_results: dict, output_path: str) -> None
    def run(self, video_path: str, job_dir: str) -> tuple[list[str], str]
```

## 処理フロー

```
動画ファイル
    │
    ▼
PySceneDetect でシーン変化フレームを検出
    │
    ▼
OpenCV で代表フレームを抽出・保存
(outputs/{job_id}/slides/slide_NNN.png)
    │
    ▼
EasyOCR で各スライド画像のテキスト認識
    │
    ▼
slides_text.txt に保存
```

## 依存ライブラリ
- `scenedetect`
- `opencv-python`
- `easyocr`
- `ffmpeg-python`

## 設定パラメータ
| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| `threshold` | `30.0` | シーン検出感度（低いほど敏感） |
| `ocr_languages` | `["ja","en"]` | OCR対象言語 |
| `min_scene_len` | `15` | 最小シーン長（フレーム数） |
