# ADR-001: 技術選定の意思決定記録

## 背景
完全ローカル・無料・CPU動作を条件に、各コンポーネントの技術を選定した。

---

## 文字起こし: faster-whisper を選択

**選択肢**
- `openai-whisper`: オリジナル実装
- `faster-whisper`: CTranslate2ベースの高速版
- `whisper.cpp`: C++実装

**理由**
- CPUでも`int8`量子化により高速動作
- Pythonから扱いやすい
- タイムスタンプ精度が高い

---

## OCR: EasyOCR を選択

**選択肢**
- `Tesseract`: 老舗OCR
- `EasyOCR`: ディープラーニングベース
- `PaddleOCR`: Baidu製

**理由**
- 日本語・英語混在テキストの認識精度が高い
- インストールが簡単（pip一発）
- Tesseractより日本語精度が優れる

---

## LLM: Ollama + qwen2.5:3b を選択

**選択肢**
- `Ollama + llama3.1:8b`: 英語中心
- `Ollama + qwen2.5:3b`: 日本語対応・軽量
- `Ollama + gemma3`: Google製

**理由**
- qwen2.5は日本語の理解・生成精度が高い
- 3bモデルはCPUでも現実的な速度で動作
- Ollamaによりモデル管理が容易

---

## Web UI: Gradio を選択

**選択肢**
- `Streamlit`: データ可視化向け
- `Gradio`: AI/MLデモ向け
- `FastAPI + React`: フルカスタム

**理由**
- ファイルアップロード・プレビューが標準搭載
- FastAPIとの連携が容易
- 最小コードで動作するUIを構築できる
