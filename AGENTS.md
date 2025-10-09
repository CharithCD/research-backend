
# GEMINI.md

## Project Overview

This project is a backend service for speech-to-text and grammar correction. It is built with Python using the FastAPI framework and is designed to be deployed with Docker.

The core functionalities are:
- **Speech-to-Text (ASR):** Transcribes audio files using the `faster-whisper` library.
- **Grammar Correction (GEC):** Corrects grammatical errors in text using a model from the Hugging Face Hub (`vennify/t5-base-grammar-correction`).
- **Phoneme Alignment:**  Analyzes and aligns phonemes in audio with a reference text.
- **API:** Exposes these functionalities through a RESTful API.
- **Database:** Stores results of GEC and phoneme analysis in a database (SQLite or PostgreSQL).
- **User Analytics:** Provides user-specific analytics on grammar and phoneme correction attempts.

The application is containerized using Docker and uses Caddy as a reverse proxy.

## Building and Running

The project is designed to be run with Docker Compose.

**Prerequisites:**
- Docker Desktop

**Steps:**

1.  **Install Docker Desktop:**
    Install Docker Desktop for your operating system.

2.  **Unzip the folder:**
    Unzip the folder to `C:\research-backend`

3.  **Open PowerShell and run the following commands:**
    ```bash
    cd C:\research-backend
    copy .env.example .env
    docker compose build
    docker compose up -d
    docker compose logs -f api
    ```
    Wait until the server is running on `0.0.0.0:8000`.

4.  **Health Check:**
    ```bash
    curl http://localhost:8000/health
    ```

## API Usage

### Grammar Correction

Corrects grammatical errors in a given text.

```bash
curl -X POST http://localhost:8000/gec/correct -H "Content-Type: application/json" -d "{\"text\":\"We discussed about the plan on Poya day.\", \"sle_mode\": true, \"return_edits\": true}"
```

### Speech-to-Text

Transcribes an audio file and corrects the grammar of the resulting text.

```bash
curl -X POST http://localhost:8000/gec/speech -F file=@sample.wav
```

### Analyze Both

Analyzes and aligns phonemes in an audio file with a reference text.

```bash
curl -s -X POST http://157.245.99.84/analyze/both \
  -F "file=@H:/short16k.wav" \
  -F "ref_text=He was happy"
  -F "user_id=test123" | jq
```

```bash
curl -X POST http://157.245.99.84/analyze/both \
    -F "file=@H:/short16k.wav" \
    -F "user_id=test123"
```

### User Analytics

Retrieves user analytics data.

```bash
curl -X GET http://157.245.99.84/analytics/test123
```

Force recompute of user analytics data.

```bash
curl -X GET http://157.245.99.84/analytics/test123?force=true
```

Recompute user analytics data.

```bash
curl -X POST http://157.245.99.84/analytics/test123/recompute
```

## Development Conventions

- **Framework:** The backend is built with [FastAPI](https://fastapi.tiangolo.com/).
- **Dependencies:** Python dependencies are managed with `pip` and are listed in `backend/requirements.txt`.
- **Configuration:** Application settings are managed through environment variables and are defined in the `backend/app/deps.py` file using `pydantic-settings`.
- **Database:** The application uses SQLAlchemy for database interaction and supports both SQLite and PostgreSQL. The database schema is defined in `backend/app/db.py`, including the new `user_analytics_cache` table for storing user-specific analytics.
- **API Schema:** API request and response models are defined in `backend/app/schemas.py` using Pydantic, including new models for user analytics data and endpoints like `/analytics/{user_id}`.
- **Containerization:** The application is containerized with Docker. The `Dockerfile` is located in the `backend` directory.
- **Reverse Proxy:** Caddy is used as a reverse proxy to the backend service. The configuration is in the `Caddyfile`.
- **CI/CD:** A GitHub Actions workflow is defined in `.github/workflows/cicd.yml` for continuous integration and deployment.
