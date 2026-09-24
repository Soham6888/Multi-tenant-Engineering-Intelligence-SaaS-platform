import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from anyio import CapacityLimiter
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette.exceptions import HTTPException

from app.api.auth import router as auth_router
from app.api.organizations import router as organizations_router
from app.core.body_limit import AuthBodyLimit
from app.core.config import Settings
from app.core.errors import error_response, http_error, validation_error
from app.services.auth_errors import AuthError
from app.services.organization_errors import OrganizationError

logger = logging.getLogger("eip.http")
logging.basicConfig(level=logging.INFO, format="%(message)s")


class HealthResponse(BaseModel):
    status: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()
    engine = create_async_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        pool_timeout=5,
        connect_args={"timeout": 3, "command_timeout": 5},
    )
    redis = Redis.from_url(
        settings.redis_url.get_secret_value(), socket_connect_timeout=2, socket_timeout=2
    )
    app.state.engine = engine
    app.state.redis = redis
    app.state.settings = settings
    app.state.sessions = async_sessionmaker(engine, expire_on_commit=False)
    app.state.password_limiter = CapacityLimiter(settings.password_hash_concurrency)
    try:
        yield
    finally:
        await redis.aclose()
        await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="Engineering Intelligence Platform", version="0.1.0", lifespan=lifespan)
    app.add_exception_handler(HTTPException, http_error)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error)  # type: ignore[arg-type]
    app.include_router(auth_router)
    app.include_router(organizations_router)
    app.add_middleware(AuthBodyLimit)

    @app.exception_handler(AuthError)
    async def auth_error(request: Request, exc: AuthError) -> Response:
        response = error_response(request, exc.status, exc.code, exc.message)
        if exc.status == 429:
            response.headers["Retry-After"] = str(request.app.state.settings.auth_window_seconds)
        return response

    @app.exception_handler(OrganizationError)
    async def organization_error(request: Request, exc: OrganizationError) -> Response:
        return error_response(request, exc.status, exc.code, exc.message)

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError) -> Response:
        logger.error(
            json.dumps(
                {
                    "event": "database_error",
                    "request_id": request.state.request_id,
                    "exception_type": type(exc).__name__,
                }
            )
        )
        return error_response(
            request, 503, "DEPENDENCY_UNAVAILABLE", "Service temporarily unavailable"
        )

    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request.state.request_id = f"req_{uuid4().hex}"
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            # Deliberately omit exception messages, query strings, headers, and bodies.
            logger.error(
                json.dumps(
                    {
                        "event": "unhandled_error",
                        "request_id": request.state.request_id,
                        "exception_type": type(exc).__name__,
                    }
                )
            )
            response = error_response(request, 500, "INTERNAL_ERROR", "An internal error occurred")
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        if request.url.path.startswith("/api/v1/auth/"):
            response.headers["Cache-Control"] = "no-store"
        logger.info(
            json.dumps(
                {
                    "event": "http_request",
                    "method": request.method,
                    "status": response.status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                    "request_id": request.state.request_id,
                }
            )
        )
        return response

    @app.get("/api/v1/health/live", response_model=HealthResponse, tags=["health"])
    async def live() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get("/api/v1/health/ready", response_model=HealthResponse, tags=["health"])
    async def ready(request: Request) -> HealthResponse | Response:
        try:
            async with asyncio.timeout(3):
                async with request.app.state.engine.connect() as connection:
                    await connection.execute(text("SELECT 1"))
                await request.app.state.redis.ping()
        except Exception:
            return error_response(
                request, 503, "DEPENDENCY_UNAVAILABLE", "A required dependency is unavailable"
            )
        return HealthResponse(status="ready")

    return app


app = create_app()
