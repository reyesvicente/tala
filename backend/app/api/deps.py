from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_session
from app.models import User
from app.services import auth
from app.services.jobs import JobRunner


def get_job_runner(request: Request) -> JobRunner:
    return request.app.state.job_runner


def get_current_user(request: Request, session: Annotated[Session, Depends(get_session)]) -> User | None:
    token = request.cookies.get(get_settings().session_cookie_name)
    return auth.user_for_session_token(session, token) if token else None


def require_user(user: Annotated[User | None, Depends(get_current_user)]) -> User:
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Log in to see this.")
    return user


CurrentUser = Annotated[User | None, Depends(get_current_user)]
RequiredUser = Annotated[User, Depends(require_user)]
