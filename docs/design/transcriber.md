# 詳細設計: Transcriber（文字起こし）

## 責務
動画・音声ファイルから音声を抽出し、テキストに変換する。

## クラス設計

```python
class Transcriber:
    def extract_audio(self, input_path: str, output_path: str) -> str
    def transcribe(self, audio_path: str, language: str) -> list[Segment]
    def save(self, segments: list[Segment], output_path: str) -> None
    def run(self, input_path: str, job_dir: str, language: str, filename_stem: str = "") -> str
```

## 処理フロー

```
入力ファイル
    │
    ├─ 動画? ──► FFmpeg で音声抽出 → temp/audio.wav
    │
    └─ 音声? ──► そのまま使用
                     │
                     ▼
              faster-whisper で文字起こし
                     │
                     ▼
              タイムスタンプ付きテキスト生成
                     │
                     ▼
              {filename_stem}_transcript.txt に保存
```

## 依存ライブラリ
- `faster-whisper`
- `ffmpeg-python`

## 設定パラメータ
| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| `model` | `small` | Whisperモデルサイズ |
| `language` | `ja` | 文字起こし言語 |
| `device` | `cpu` | 処理デバイス |
| `compute_type` | `int8` | 量子化設定（CPU高速化） |
