FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1

# System deps for audio and Whisper
RUN apt-get update && apt-get install -y --no-install-recommends     libsndfile1 ffmpeg git libgomp1 &&     rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip &&     pip install -r requirements.txt &&     pip install --index-url https://download.pytorch.org/whl/cpu torch==2.3.1

COPY app ./app

EXPOSE 8000

# ... your existing Dockerfile ...
RUN python - <<'PY'
import nltk, os
os.makedirs("/root/nltk_data", exist_ok=True)
nltk.download('averaged_perceptron_tagger', download_dir='/root/nltk_data')
nltk.download('cmudict', download_dir='/root/nltk_data')
PY
ENV NLTK_DATA=/root/nltk_data

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
