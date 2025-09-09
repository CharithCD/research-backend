FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/root/.cache/huggingface

# Minimal system deps + s3cmd (for DigitalOcean Spaces)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 ffmpeg git s3cmd && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install CPU-only torch first (prevents heavy CUDA wheels)
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r /app/requirements.txt

# App code (expects this Dockerfile at backend/ and build context = repo root)
COPY backend /app

# Bootstrap script will fetch model from DO Spaces on container start
RUN chmod +x /app/bootstrap_model.sh

# Preload NLTK assets used by g2p_en
RUN python - <<'PY'
import nltk, os
os.makedirs("/root/nltk_data", exist_ok=True)
nltk.download('averaged_perceptron_tagger', download_dir='/root/nltk_data')
nltk.download('cmudict', download_dir='/root/nltk_data')
PY
ENV NLTK_DATA=/root/nltk_data

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 ffmpeg git s3cmd && \
    rm -rf /var/lib/apt/lists/*


EXPOSE 8000

# Pull model if missing, then run API
CMD /app/bootstrap_model.sh && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
