import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.transcriptions import router as transcriptions_router
from app.config import get_settings
from app.db import SessionLocal
from app.services.jobs import JobRunner

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    runner = getattr(app.state, "job_runner", None) or JobRunner(SessionLocal)
    app.state.job_runner = runner
    runner.start()
    yield
    runner.stop()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Tala", lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json")

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.exception_handler(HTTPException)
    async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"data": None, "message": exc.detail, "errors": None},
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"data": None, "message": "Invalid request.", "errors": exc.errors()},
        )

    @app.get("/api/health")
    def health() -> dict:
        return {"data": {"ok": True}, "message": "", "errors": None}

    app.include_router(auth_router)
    app.include_router(transcriptions_router)

    dist = settings.frontend_dist
    if dist and dist.is_dir():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def spa(path: str) -> FileResponse:
            if path.startswith("api/"):
                raise HTTPException(404, "Not found.")
            candidate = (dist / path).resolve()
            if path and candidate.is_file() and candidate.is_relative_to(dist.resolve()):
                return FileResponse(candidate)
            return FileResponse(dist / "index.html")

    return app


app = create_app()
