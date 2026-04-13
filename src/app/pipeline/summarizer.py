"""
Summarizer: 文字起こしとスライドテキストから要約・議事録を生成する
仕様: docs/design/summarizer.md
"""
from pathlib import Path

import httpx

from app.utils.logger import get_logger

logger = get_logger(__name__)

# 文字起こしが長い場合のチャンク要約プロンプト
CHUNK_PROMPT = """\
あなたは議事録作成の専門家です。
以下は会議の文字起こしの一部（{index}/{total}）です。日本語で発言内容の要点を箇条書きでまとめてください。

## 文字起こし（{index}/{total}）
{chunk}

## 指示
- 発言の要点を箇条書きで列挙してください
- 決定事項・アクションアイテムがあれば明記してください
- スクリーンショットやカメラ映像の説明は除いてください
"""

SUMMARY_PROMPT = """\
あなたは議事録作成の専門家です。
以下の会議の文字起こし要点とスライド内容をもとに、日本語で要約を作成してください。

## 文字起こしの要点
{transcript_summary}

## スライド内容（参考）
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

# 1チャンクあたりの文字数（約2000トークン相当）
CHUNK_SIZE = 3000


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
            "options": {"num_predict": self.max_tokens, "num_ctx": 4096},
        }
        logger.info(f"Ollama呼び出し: {self.model}")
        resp = httpx.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()["response"]

    def _chunk_transcript(self, transcript: str) -> list[str]:
        """文字起こしをCHUNK_SIZE文字ごとに分割する"""
        chunks = []
        for i in range(0, len(transcript), CHUNK_SIZE):
            chunks.append(transcript[i:i + CHUNK_SIZE])
        return chunks

    def _summarize_chunks(self, transcript: str) -> str:
        """長い文字起こしをチャンクに分けて要約する"""
        chunks = self._chunk_transcript(transcript)
        total = len(chunks)
        logger.info(f"文字起こしをチャンク分割: {total}チャンク")

        chunk_summaries = []
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"チャンク要約中: {i}/{total}")
            prompt = CHUNK_PROMPT.format(index=i, total=total, chunk=chunk)
            summary = self._call_ollama(prompt)
            chunk_summaries.append(f"### パート{i}\n{summary}")

        return "\n\n".join(chunk_summaries)

    def generate_summary(self, transcript_path: Path, slides_text_path: Path) -> str:
        transcript = transcript_path.read_text(encoding="utf-8") if transcript_path.exists() else ""
        slides_text = slides_text_path.read_text(encoding="utf-8") if slides_text_path.exists() else ""

        # 文字起こしが長い場合はチャンク処理
        if len(transcript) > CHUNK_SIZE:
            logger.info(f"文字起こしが長いためチャンク処理を行います ({len(transcript)}文字)")
            transcript_summary = self._summarize_chunks(transcript)
        else:
            transcript_summary = transcript

        # スライドテキストは先頭2000文字のみ使用
        slides_text_trimmed = slides_text[:2000] if len(slides_text) > 2000 else slides_text

        prompt = SUMMARY_PROMPT.format(
            transcript_summary=transcript_summary,
            slides_text=slides_text_trimmed,
        )
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
