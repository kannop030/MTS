#!/bin/bash
# 初回セットアップスクリプト
set -e

echo "=== Media Transcriber セットアップ ==="

# データディレクトリ作成
mkdir -p data/uploads data/outputs data/temp data/models

# Ollamaモデルダウンロード（初回のみ）
echo "Ollamaモデルをダウンロード中: qwen2.5:3b"
docker compose run --rm ollama ollama pull qwen2.5:3b

echo "=== セットアップ完了 ==="
echo "起動コマンド: docker compose up"
