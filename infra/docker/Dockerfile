FROM python:3.11-slim

# システム依存パッケージ（FFmpeg・OpenCV用）
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU版PyTorchを先にインストール（easyocrがCUDA版を引き込まないように）
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 依存パッケージインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードコピー
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY config/ ./config/

# データディレクトリ作成
RUN mkdir -p data/uploads data/outputs data/temp

# Pythonモジュールパス設定
ENV PYTHONPATH=/app/src

EXPOSE 8000 7860

CMD ["python", "src/app/main.py"]
