
# GEMINI.md

## Project Overview

This project is a backend service for speech-to-text and grammar correction. It is built with Python using the FastAPI framework and is designed to be deployed with Docker.

The core functionalities are:
- **Speech-to-Text (ASR):** Transcribes audio files using the `faster-whisper` library.
- **Grammar Correction (GEC):** Corrects grammatical errors in text using a model from the Hugging Face Hub (`vennify/t5-base-grammar-correction`).
- **Phoneme Alignment:**  Analyzes and aligns phonemes in audio with a reference text.
- **API:** Exposes these functionalities through a RESTful API.
- **Database:** Stores results of GEC and phoneme analysis in a database (SQLite or PostgreSQL).

The application is containerized using Docker and uses Caddy as a reverse proxy.

## Building and Running

The project is designed to be run with Docker Compose.

**Prerequisites:**
- Docker Desktop

**Steps:**

1.  **Create Environment File:**
    ```bash
    copy .env.example .env
    ```

2.  **Build and Run:**
    ```bash
    docker compose build
    docker compose up -d
    ```

3.  **Check Logs:**
    ```bash
    docker compose logs -f api
    ```
    Wait until the server is running on `0.0.0.0:8000`.

4.  **Health Check:**
    ```bash
    curl http://localhost:8000/health
    ```

## Development Conventions

- **Framework:** The backend is built with [FastAPI](https://fastapi.tiangolo.com/).
- **Dependencies:** Python dependencies are managed with `pip` and are listed in `backend/requirements.txt`.
- **Configuration:** Application settings are managed through environment variables and are defined in the `backend/app/deps.py` file using `pydantic-settings`.
- **Database:** The application uses SQLAlchemy for database interaction and supports both SQLite and PostgreSQL. The database schema is defined in `backend/app/db.py`.
- **API Schema:** API request and response models are defined in `backend/app/schemas.py` using Pydantic.
- **Containerization:** The application is containerized with Docker. The `Dockerfile` is located in the `backend` directory.
- **Reverse Proxy:** Caddy is used as a reverse proxy to the backend service. The configuration is in the `Caddyfile`.
- **CI/CD:** A GitHub Actions workflow is defined in `.github/workflows/cicd.yml` for continuous integration and deployment.
