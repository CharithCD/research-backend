TINY SPEECH→GEC BACKEND (Docker, CPU)

1) Install Docker Desktop (Windows 11). Start it.
2) Unzip this folder to: C:\research-backend
3) Open PowerShell and run:
   cd C:\research-backend
   copy .env.example .env
   docker compose build
   docker compose up -d
   docker compose logs -f api
   (wait until server shows it's running on 0.0.0.0:8000)

4) Health check:
   curl http://localhost:8000/health

5) Grammar (text → JSON):
   curl -X POST http://localhost:8000/gec/correct -H "Content-Type: application/json" -d "{\"text\":\"We discussed about the plan on Poya day.\", \"sle_mode\": true, \"return_edits\": true}"

6) Audio → JSON (Whisper tiny + GEC):
   curl -X POST http://localhost:8000/gec/speech -F file=@sample.wav

Notes:
- First run downloads models; be patient.
- This build uses: Whisper tiny (CPU int8) and vennify/t5-base-grammar-correction (CPU).
- To switch grammar model later, edit .env and rebuild.
