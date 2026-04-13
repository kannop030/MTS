# 詳細設計: Summarizer（要約・議事録生成）

## 責務
文字起こしテキストとスライドテキストを入力に、要約と議事録をOllamaで生成する。

## クラス設計

```python
class Summarizer:
    def build_summary_prompt(self, transcript: str, slides_text: str) -> str
    def build_minutes_prompt(self, summary: str) -> str
    def call_ollama(self, prompt: str) -> str
    def generate_summary(self, transcript_path: str, slides_text_path: str) -> str
    def generate_minutes(self, summary: str) -> str
    def run(self, job_dir: str, filename_stem: str = "") -> tuple[str, str]
```

## 処理フロー

```
{filename_stem}_transcript.txt + {filename_stem}_slides_text.txt
    │
    ▼
プロンプト構築（要約用）
    │
    ▼
Ollama API 呼び出し（qwen2.5:3b）
    │
    ▼
{filename_stem}_summary.md 保存
    │
    ▼
プロンプト構築（議事録用）
    │
    ▼
Ollama API 呼び出し
    │
    ▼
{filename_stem}_minutes.md 保存
```

## プロンプトテンプレート

### 要約プロンプト
```
あなたは優秀なアシスタントです。
以下の文字起こしとスライド内容を読み、日本語で要点をまとめてください。

## 文字起こし
{transcript}

## スライド内容
{slides_text}

## 出力形式
Markdown形式で、概要・主なトピック・重要なポイントの構成でまとめてください。
```

### 議事録プロンプト
```
以下の要約をもとに、議事録を日本語で作成してください。

## 要約
{summary}

## 出力形式
Markdown形式で、基本情報・主要トピック・決定事項・TODOを含めてください。
```

## 依存ライブラリ
- `httpx`（Ollama API呼び出し）

## 設定パラメータ
| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| `base_url` | `http://ollama:11434` | Ollama APIのURL |
| `model` | `qwen2.5:3b` | 使用モデル |
| `timeout` | `120` | APIタイムアウト秒数 |
| `max_tokens` | `4096` | 最大出力トークン数 |
