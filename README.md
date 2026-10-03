# Tala — audio to text, no signup

Free audio/video → text transcription. No account, no credit card. Built for Paolo for the
DEV Hacktoberfest Weekend Challenge ("Build for a Friend").

- **Open-weight model:** OpenAI Whisper via [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
  (CTranslate2, int8 on CPU). No third-party AI API is called.
- **Privacy:** audio is deleted the moment it's transcribed; transcripts self-destruct after
  `RETENTION_HOURS` (default 72). Access is by unguessable link only.
- Upload a file or record in the browser · auto-detect ~100 languages · translate to English ·
  export TXT / SRT / WebVTT.

## Stack

| | |
|---|---|
| API | FastAPI, SQLAlchemy 2, Alembic, PostgreSQL |
| Transcription | faster-whisper, single in-process worker thread (jobs resume after restart) |
| Frontend | React 18 + Vite + TypeScript, TanStack Query, Zustand, React Hook Form + Zod, ice-ds, Tailwind |

## Run locally

```bash
cp .envs/.local/.api.example .envs/.local/.api
cp .envs/.local/.postgres.example .envs/.local/.postgres

docker compose -f docker-compose.local.yml up --build   # API on :8000, runs migrations on start
cd frontend && npm install && npm run dev                # http://localhost:5173 (proxies /api)
```

The first transcription downloads the Whisper model (~150 MB for `base`) into a Docker volume.
Pick a different size with `WHISPER_MODEL` (`tiny`, `base`, `small`, `medium`, `large-v3`).

### Backend commands

```bash
docker compose -f docker-compose.local.yml run --rm api pytest
docker compose -f docker-compose.local.yml run --rm api ruff check .
docker compose -f docker-compose.local.yml run --rm api alembic revision --autogenerate -m "..."
```

## API

All JSON responses use `{ "data": ..., "message": "", "errors": null }`.

| Method | Path | |
|---|---|---|
| `GET` | `/api/info` | model, limits, language list |
| `POST` | `/api/transcriptions` | multipart: `file`, optional `language`, `task` (`transcribe`/`translate`) → 202 |
| `GET` | `/api/transcriptions/{slug}` | status, progress, text, segments |
| `GET` | `/api/transcriptions/{slug}/export/{txt,srt,vtt}` | download |
| `DELETE` | `/api/transcriptions/{slug}` | delete now |

OpenAPI docs: http://localhost:8000/api/docs

## Production

`compose/production/Dockerfile` builds a single image (frontend baked in, model pre-downloaded) that
serves the SPA and API from one origin. It needs `DATABASE_URL` and honors `PORT`.
