# Media Transcriber & Summarizer

会議録画・講義動画・音声データから、文字起こし・スライド抽出・要約・議事録生成を
完全ローカルで自動化するシステム。

## 特徴
- 完全ローカル動作（データの外部送信なし）
- 無料（有償API不使用）
- Docker対応
- 日本語対応
- フォルダ監視モード対応（ファイルを置くだけで自動処理）

## ドキュメント

| ファイル | 内容 |
|----------|------|
| [00_overview](docs/spec/00_overview.md) | システム概要 |
| [01_requirements](docs/spec/01_requirements.md) | 要件定義 |
| [02_architecture](docs/spec/02_architecture.md) | アーキテクチャ設計 |
| [03_api_spec](docs/spec/03_api_spec.md) | API仕様 |
| [04_pipeline_spec](docs/spec/04_pipeline_spec.md) | 処理パイプライン仕様 |
| [05_data_schema](docs/spec/05_data_schema.md) | 入出力データ仕様 |

## 起動方法

### Web UI モード（通常）

```bash
docker compose up
```

ブラウザで `http://localhost:7860` にアクセス。

### フォルダ監視モード

```bash
# 基本起動（設定は config/settings.yaml から読み込み）
python scripts/watch.py

# オプション指定
python scripts/watch.py --language en --ocr --minutes

# 監視フォルダを変更
python scripts/watch.py --watch-dir /path/to/folder
```

`data/watch/` にファイルを置くと自動で処理が始まり、結果は `data/outputs/` に保存されます。
処理が正常完了したファイルは自動で削除されます。失敗した場合は `data/watch/failed/` に移動します。

## ログ

アプリ起動時に `logs/media_transcriber.log` へ自動出力されます。
ログは日次でローテーションされ、90日（3か月）を超えたファイルは起動時に自動削除されます。

設定は `config/settings.yaml` の `logging` セクションで変更できます。

```yaml
logging:
  log_dir: "logs"                   # 出力ディレクトリ
  log_file: "media_transcriber.log" # ファイル名
  log_level: "INFO"                 # ログレベル (DEBUG / INFO / WARNING / ERROR)
  retention_days: 90                # 保持日数
```

## 技術スタック
- 文字起こし: faster-whisper
- 動画処理: FFmpeg + OpenCV + PySceneDetect
- OCR: EasyOCR
- 要約・議事録: Ollama (qwen2.5:3b)
- Web UI: Gradio
- API: FastAPI
- フォルダ監視: watchdog
