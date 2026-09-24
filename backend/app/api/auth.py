import secrets
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.rate_limit import check_auth_limit
from app.core.security import csrf_value
from app.models import User
from app.repositories.auth import AuthRepository
from app.schemas.auth import LoginInput, RegisterInput, SessionOutput, UserOutput
from app.services.auth import AuthService
from app.services.auth_errors import AuthError

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


def settings_for(request: Request) -> Settings:
    return request.app.state.settings  # type: ignore[no-any-return]


async def database(request: Request) -> AsyncIterator[AsyncSession]:
    try:
        async with request.app.state.sessions() as db:
            yield db
    except (SQLAlchemyError, OSError, TimeoutError) as exc:
        raise AuthError(
            503, "DEPENDENCY_UNAVAILABLE", "Authentication is temporarily unavailable"
        ) from exc


def auth_service(
    request: Request,
    db: Annotated[AsyncSession, Depends(database)],
    settings: Annotated[Settings, Depends(settings_for)],
) -> AuthService:
    return AuthService(AuthRepository(db), settings, request.app.state.password_limiter)


def browser_mutation(
    request: Request, settings: Annotated[Settings, Depends(settings_for)]
) -> None:
    if request.headers.get("origin") not in settings.allowed_origins:
        raise AuthError(403, "ORIGIN_REJECTED", "Request origin is not allowed")
    if request.headers.get("x-eip-request") != "1":
        raise AuthError(403, "CSRF_REJECTED", "Request verification failed")


async def current_user(
    request: Request, service: Annotated[AuthService, Depends(auth_service)]
) -> User:
    _, user = await service.authenticate(request.cookies.get(service.settings.cookie_name))
    return user


async def rate_limit(request: Request, email: str | None = None) -> None:
    await check_auth_limit(
        request.app.state.redis,
        request.app.state.settings,
        request.client.host if request.client else "unknown",
        email,
    )


def set_session(response: Response, settings: Settings, token: str) -> None:
    response.set_cookie(
        settings.cookie_name,
        token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        path="/",
    )


@router.post(
    "/register",
    status_code=201,
    response_model=SessionOutput,
    dependencies=[Depends(browser_mutation)],
)
async def register(
    data: RegisterInput,
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(auth_service)],
) -> SessionOutput:
    await rate_limit(request, str(data.email))
    user, token = await service.register(
        data, request.state.request_id, request.cookies.get(service.settings.cookie_name)
    )
    set_session(response, service.settings, token)
    return SessionOutput(user=UserOutput.model_validate(user), csrf_token=csrf_value(token))


@router.post("/login", response_model=SessionOutput, dependencies=[Depends(browser_mutation)])
async def login(
    data: LoginInput,
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(auth_service)],
) -> SessionOutput:
    await rate_limit(request, str(data.email))
    user, token = await service.login(
        data, request.state.request_id, request.cookies.get(service.settings.cookie_name)
    )
    set_session(response, service.settings, token)
    return SessionOutput(user=UserOutput.model_validate(user), csrf_token=csrf_value(token))


@router.get("/me", response_model=SessionOutput)
async def me(
    request: Request,
    user: Annotated[User, Depends(current_user)],
    settings: Annotated[Settings, Depends(settings_for)],
) -> SessionOutput:
    token = request.cookies[settings.cookie_name]
    return SessionOutput(user=UserOutput.model_validate(user), csrf_token=csrf_value(token))


@router.post("/logout", status_code=204, dependencies=[Depends(browser_mutation)])
async def logout(
    request: Request, response: Response, service: Annotated[AuthService, Depends(auth_service)]
) -> None:
    await rate_limit(request)
    token = request.cookies.get(service.settings.cookie_name, "")
    supplied = request.headers.get("x-csrf-token", "")
    if not token or not secrets.compare_digest(supplied, csrf_value(token)):
        raise AuthError(403, "CSRF_REJECTED", "Request verification failed")
    await service.logout(token, request.state.request_id)
    response.delete_cookie(
        service.settings.cookie_name,
        path="/",
        httponly=True,
        secure=service.settings.environment == "production",
        samesite="lax",
    )
