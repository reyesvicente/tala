FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY backend/requirements /requirements
RUN pip install -r /requirements/local.txt

COPY compose/local/api/start.sh /start.sh
RUN chmod +x /start.sh

COPY backend /app

CMD ["/start.sh"]
