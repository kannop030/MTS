# Media Transcriber & Summarizer

会議録画・講義動画・音声データから、文字起こし・スライド抽出・要約・議事録生成を
完全ローカルで自動化するシステム。

## 特徴
- 完全ローカル動作（データの外部送信なし）
- 無料（有償API不使用）
- Docker対応
- 日本語対応

## ドキュメント

| ファイル | 内容 |
|----------|------|
| [00_overview](docs/spec/00_overview.md) | システム概要 |
| [01_requirements](docs/spec/01_requirements.md) | 要件定義 |
| [02_architecture](docs/spec/02_architecture.md) | アーキテクチャ設計 |
| [03_api_spec](docs/spec/03_api_spec.md) | API仕様 |
| [04_pipeline_spec](docs/spec/04_pipeline_spec.md) | 処理パイプライン仕様 |
| [05_data_schema](docs/spec/05_data_schema.md) | 入出力データ仕様 |

## 起動方法（構築後）

```bash
docker compose up
```

ブラウザで `http://localhost:7860` にアクセス。

## 技術スタック
- 文字起こし: faster-whisper
- 動画処理: FFmpeg + OpenCV + PySceneDetect
- OCR: EasyOCR
- 要約・議事録: Ollama (qwen2.5:3b)
- Web UI: Gradio
- API: FastAPI
