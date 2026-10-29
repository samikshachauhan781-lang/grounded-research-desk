"""FastAPI application entrypoint."""

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.routes import (
    ask,
    collections,
    documents,
    evaluations,
    health,
    research,
    search,
    sessions,
    system,
)
from backend.app.core.config import Settings, get_settings
from backend.app.core.dependencies import settings_dep
from backend.app.core.exceptions import AppError
from backend.app.core.logging import configure_logging
from backend.app.database.session import configure_database, init_database
from backend.app.models.schemas import ErrorEnvelope, ErrorBody

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    configure_database(resolved)

    @asynccontextmanager
    async def app_lifespan(app: FastAPI):
        configure_logging(resolved)
        init_database()
        logger.info("event=startup app=%s env=%s", resolved.app_name, resolved.app_env)
        yield
        logger.info("event=shutdown app=%s", resolved.app_name)

    app = FastAPI(
        title="Grounded Research Desk",
        version=resolved.app_version,
        lifespan=app_lifespan,
        docs_url="/docs" if resolved.app_env == "development" else None,
        redoc_url=None,
    )
    app.state.settings = resolved

    def resolved_settings() -> Settings:
        return app.state.settings

    app.dependency_overrides[settings_dep] = resolved_settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        envelope = ErrorEnvelope(
            error=ErrorBody(
                code=exc.code,
                message=exc.message,
                details=exc.details,
                request_id=getattr(request.state, "request_id", None),
            ),
        )
        return JSONResponse(status_code=exc.status_code, content=envelope.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception("event=error request_id=%s", getattr(request.state, "request_id", None))
        envelope = ErrorEnvelope(
            error=ErrorBody(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred.",
                request_id=getattr(request.state, "request_id", None),
            ),
        )
        return JSONResponse(status_code=500, content=envelope.model_dump())

    app.include_router(health.router)
    api = resolved.api_prefix.rstrip("/")
    app.include_router(documents.router, prefix=api)
    app.include_router(search.router, prefix=api)
    app.include_router(ask.router, prefix=api)
    app.include_router(collections.router, prefix=api)
    app.include_router(sessions.router, prefix=api)
    app.include_router(evaluations.router, prefix=api)
    app.include_router(research.router, prefix=api)
    app.include_router(system.router, prefix=api)

    return app


app = create_app()
