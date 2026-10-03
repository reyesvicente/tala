"""Transactional email via Resend's HTTP API. Falls back to logging when no API key is set."""

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"


def send_email(to: str, subject: str, text: str) -> None:
    settings = get_settings()
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not set; email to %s not sent.\nSubject: %s\n%s", to, subject, text)
        return
    try:
        response = httpx.post(
            RESEND_URL,
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={"from": settings.email_from, "to": [to], "subject": subject, "text": text},
            timeout=10,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        logger.exception("Failed to send email to %s", to)
