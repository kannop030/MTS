FROM python:3.11-slim

# システム依存パッケージ（FFmpeg・OpenCV用）
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 依存パッケージインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードコピー
COPY src/ ./src/
COPY config/ ./config/

# データディレクトリ作成
RUN mkdir -p data/uploads data/outputs data/temp

EXPOSE 8000 7860

CMD ["python", "src/app/main.py"]
