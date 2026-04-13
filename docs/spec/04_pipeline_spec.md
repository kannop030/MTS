# 処理パイプライン仕様

## パイプライン全体フロー

```
入力ファイル判定
    │
    ├─ 動画ファイル ──► ステップ1: 音声抽出
    │                        │
    ├─ 音声ファイル ──────────┤
    │                        ▼
    │                  ステップ2: 文字起こし（Whisper）
    │                        │
    ├─ 動画ファイル ──► ステップ3: フレーム抽出
    │                        │
    │                  ステップ4: スライド検出（PySceneDetect）
    │                        │
    │                  ステップ5: OCR（EasyOCR）
    │                        │
    └─ テキストファイル ───────┤
                             ▼
                       ステップ6: 要約生成（Ollama）
                             │
                       ステップ7: 議事録生成（Ollama）
                             │
                           出力
```

---

## ステップ詳細

### ステップ1: 音声抽出
- **ツール**: FFmpeg
- **入力**: 動画ファイル
- **出力**: `temp/audio.wav`（16kHz, モノラル）
- **コマンド例**:
  ```
  ffmpeg -i input.mp4 -ar 16000 -ac 1 -f wav temp/audio.wav
  ```

---

### ステップ2: 文字起こし
- **ツール**: faster-whisper
- **モデル**: `small`（CPU環境での速度・精度バランス）
- **入力**: `temp/audio.wav`
- **出力**: `outputs/{job_id}/transcript.txt`
- **出力形式**:
  ```
  [00:00:05 --> 00:00:12] こんにちは、本日の会議を始めます。
  [00:00:13 --> 00:00:20] 最初のアジェンダは先週の振り返りです。
  ```

---

### ステップ3: フレーム抽出
- **ツール**: FFmpeg + OpenCV
- **入力**: 動画ファイル
- **処理**: 1秒ごとにフレームを一時保存
- **出力**: `temp/frames/frame_{n:04d}.png`

---

### ステップ4: スライド検出
- **ツール**: PySceneDetect（ContentDetector）
- **入力**: `temp/frames/`
- **閾値**: 30.0（調整可能）
- **処理**: シーン変化点を検出し、代表フレームを選択
- **出力**: `outputs/{job_id}/slides/slide_{n:03d}.png`

---

### ステップ5: OCR
- **ツール**: EasyOCR
- **言語**: `['ja', 'en']`
- **入力**: `outputs/{job_id}/slides/*.png`
- **出力**: `outputs/{job_id}/slides_text.txt`
- **出力形式**:
  ```
  --- slide_001.png ---
  アジェンダ
  1. 先週の振り返り
  2. 今週の目標
  ```

---

### ステップ6: 要約生成
- **ツール**: Ollama API
- **モデル**: `qwen2.5:3b`
- **入力**: transcript.txt + slides_text.txt
- **処理方式**: 文字起こしが3000文字を超える場合、チャンク処理を行う
  1. 文字起こしを3000文字ごとに分割
  2. 各チャンクをOllamaで個別に要約（箇条書き）
  3. 全チャンクの要約 + スライド内容（先頭2000文字）を合わせて最終要約を生成
- **優先度**: 文字起こしを主軸とし、スライドは参考情報として扱う
- **プロンプト構造**:
  ```
  ## 文字起こしの要点        ← チャンク要約の結果
  {transcript_summary}
  ## スライド内容（参考）    ← slides_text.txt の先頭2000文字
  {slides_text}
  ```
- **出力**: `outputs/{job_id}/summary.md`

---

### ステップ7: 議事録生成
- **ツール**: Ollama API
- **モデル**: `qwen2.5:3b`
- **入力**: summary.md
- **出力形式**:
  ```markdown
  # 議事録
  ## 基本情報
  - 日時:
  - 概要:
  ## 主要トピック
  ## 決定事項
  ## TODO・アクションアイテム
  ```
- **出力**: `outputs/{job_id}/minutes.md`

---

## 設定パラメータ（config/settings.yaml）

```yaml
whisper:
  model: "small"       # tiny / base / small / medium / large
  language: "ja"       # ja / en / auto

scene_detect:
  threshold: 30.0      # シーン変化の感度（低いほど敏感）

ocr:
  languages: ["ja", "en"]

ollama:
  base_url: "http://ollama:11434"
  model: "qwen2.5:3b"
  timeout: 3600   # 60分（長い文字起こしのチャンク処理に対応）
  max_tokens: 4096

output:
  format: "markdown"
```
