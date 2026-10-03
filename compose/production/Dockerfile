# Single image: builds the React frontend, then serves it + the API from FastAPI.
FROM node:24-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FRONTEND_DIST=/app/static \
    WHISPER_MODEL_DIR=/models \
    UPLOAD_DIR=/data/uploads
WORKDIR /app
COPY backend/requirements /requirements
RUN pip install -r /requirements/production.txt
COPY backend /app
COPY --from=frontend /frontend/dist /app/static
# Bake the model into the image so cold starts don't download it.
ARG WHISPER_MODEL=base
ENV WHISPER_MODEL=${WHISPER_MODEL}
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('${WHISPER_MODEL}', device='cpu', compute_type='int8', download_root='/models')"
# Model is baked in: never call out to the Hugging Face Hub at runtime.
ENV HF_HUB_OFFLINE=1
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
