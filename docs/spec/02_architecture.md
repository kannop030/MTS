# アーキテクチャ設計

## システム全体図

```
┌──────────────────────────────────────────────────────────────┐
│                        ユーザーのPC                           │
│                                                              │
│  ブラウザ                    data/watch/（ファイルを置く）    │
│  └─ http://localhost:7860         │                          │
│         │                         │ ファイル検知             │
│  ┌──────▼───────────────────┐ ┌───▼────────────────────┐   │
│  │   Gradio Web UI (7860)   │ │  FolderWatcher         │   │
│  └──────────────────────────┘ │  (scripts/watch.py)    │   │
│         │ HTTP                └───────────┬────────────┘   │
│  ┌──────▼───────────────────────────────────────────────┐   │
│  │               FastAPI Backend (Port 8000)              │   │
│  │                                                        │   │
│  │  ┌─────────────┐ ┌──────────────┐ ┌───────────────┐  │   │
│  │  │ Transcriber │ │  Extractor   │ │  Summarizer   │  │   │
│  │  │faster-whisper│ │FFmpeg+OpenCV│ │ Ollama API    │  │   │
│  │  │             │ │+PySceneDetect│ │ (localhost)   │  │   │
│  │  │             │ │+EasyOCR      │ │               │  │   │
│  │  └─────────────┘ └──────────────┘ └───────────────┘  │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐   │
│  │              Ollama Server (Port 11434)                │   │
│  │              モデル: qwen2.5:3b                        │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  data/watch/    data/outputs/    data/temp/                  │
└──────────────────────────────────────────────────────────────┘
```

## コンポーネント構成

### Gradio Web UI
- ファイルアップロード
- 処理オプション選択（文字起こしは必須・OCR/要約議事録はチェックボックスで任意選択）
- 進捗表示
- 結果プレビューとダウンロード

### FastAPI Backend
- `/api/upload` : ファイル受け取り
- `/api/process` : 処理実行（非同期）
- `/api/status/{job_id}` : 進捗確認
- `/api/download/{job_id}` : 結果取得

### Transcriber（文字起こし）
- 動画から音声を抽出（FFmpeg）
- faster-whisperで文字起こし
- タイムスタンプ付きテキストを出力

### Extractor（スライド抽出）
- PySceneDetectでシーン変化を検出
- OpenCVで代表フレームを抽出・保存
- EasyOCRでスライドテキストを認識

### Summarizer（要約・議事録）
- 文字起こし＋スライドテキストを結合
- Ollama APIへプロンプトを送信
- 要約・議事録をMarkdownで出力

### FolderWatcher（フォルダ監視）
- `watchdog` ライブラリで `data/watch/` をリアルタイム監視
- 対応ファイル検知後、書き込み完了を確認してからパイプラインを直接呼び出す
- 処理成功時: 元ファイルを削除
- 処理失敗時: `data/watch/failed/` へ移動
- `scripts/watch.py` から起動（FastAPI サーバー不要）

## Docker構成

```yaml
services:
  app:        # FastAPI + Gradio
  ollama:     # Ollamaサーバー
```

## データフロー

```
入力ファイル
    │
    ▼
[uploads/]
    │
    ▼
Transcriber【必須】
    │
    ▼
transcript.txt
    │
    ├─ enable_ocr=true かつ動画 ──► Extractor【任意】
    │                                    │
    │                             slides/*.png
    │                             slides_text.txt
    │                                    │
    ├─ enable_minutes=true ──────────────┴──► Summarizer【任意】
    │                                              │
    │                                    ┌─────────┴──────────┐
    │                                    ▼                    ▼
    │                                summary.md          minutes.md
    │
    └──► 出力（transcript.txt は常に生成）
```
