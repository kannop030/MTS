"""
Summarizer: 文字起こしとスライドテキストから要約・議事録を生成する
仕様: docs/design/summarizer.md
"""
from pathlib import Path

import httpx

from app.utils.logger import get_logger

logger = get_logger(__name__)

SUMMARY_PROMPT = """\
あなたは優秀なアシスタントです。
以下の文字起こしとスライド内容を読み、日本語で要点をまとめてください。

## 文字起こし
{transcript}

## スライド内容
{slides_text}

## 出力形式
Markdown形式で、以下の構成でまとめてください。
# 要約
## 概要
## 主なトピック
## 重要なポイント
"""

MINUTES_PROMPT = """\
以下の要約をもとに、議事録を日本語で作成してください。

## 要約
{summary}

## 出力形式
Markdown形式で、以下の構成で作成してください。
# 議事録
## 基本情報
- タイトル:
- 日時:
- 概要:
## 主要トピック
## 決定事項
## TODO・アクションアイテム
"""


class Summarizer:
    def __init__(self, settings: dict):
        cfg = settings["ollama"]
        self.base_url = cfg["base_url"]
        self.model = cfg["model"]
        self.timeout = cfg["timeout"]
        self.max_tokens = cfg["max_tokens"]

    def _call_ollama(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": self.max_tokens},
        }
        logger.info(f"Ollama呼び出し: {self.model}")
        resp = httpx.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()["response"]

    def generate_summary(self, transcript_path: Path, slides_text_path: Path) -> str:
        transcript = transcript_path.read_text(encoding="utf-8") if transcript_path.exists() else ""
        slides_text = slides_text_path.read_text(encoding="utf-8") if slides_text_path.exists() else ""
        prompt = SUMMARY_PROMPT.format(transcript=transcript, slides_text=slides_text)
        return self._call_ollama(prompt)

    def generate_minutes(self, summary: str) -> str:
        prompt = MINUTES_PROMPT.format(summary=summary)
        return self._call_ollama(prompt)

    def run(self, job_dirs: dict) -> tuple[Path, Path]:
        transcript_path  = job_dirs["output"] / "transcript.txt"
        slides_text_path = job_dirs["output"] / "slides_text.txt"

        logger.info("要約生成中")
        summary = self.generate_summary(transcript_path, slides_text_path)
        summary_path = job_dirs["output"] / "summary.md"
        summary_path.write_text(summary, encoding="utf-8")
        logger.info(f"要約保存: {summary_path}")

        logger.info("議事録生成中")
        minutes = self.generate_minutes(summary)
        minutes_path = job_dirs["output"] / "minutes.md"
        minutes_path.write_text(minutes, encoding="utf-8")
        logger.info(f"議事録保存: {minutes_path}")

        return summary_path, minutes_path
