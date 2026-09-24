import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from anyio import CapacityLimiter, to_thread
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings
from app.core.security import DUMMY_HASH, hash_password, token_digest, verify_password
from app.models import AuditLog, Session, User
from app.repositories.auth import AuthRepository
from app.schemas.auth import LoginInput, RegisterInput
from app.services.auth_errors import AuthError


class AuthService:
    def __init__(
        self, repository: AuthRepository, settings: Settings, limiter: CapacityLimiter
    ) -> None:
        self.repository = repository
        self.settings = settings
        self.limiter = limiter

    async def register(
        self, data: RegisterInput, request_id: str, previous: str | None
    ) -> tuple[User, str]:
        hashed = await to_thread.run_sync(
            hash_password, data.password.get_secret_value(), limiter=self.limiter
        )
        user = User(id=uuid4(), email=str(data.email), name=data.name, password_hash=hashed)
        self.repository.db.add(user)
        try:
            await self.repository.db.flush()
        except IntegrityError as exc:
            await self.repository.db.rollback()
            # Only the expected email uniqueness violation is a registration conflict.
            cause = getattr(exc.orig, "sqlstate", None)
            if cause == "23505":
                raise AuthError(
                    409, "REGISTRATION_UNAVAILABLE", "Unable to register with these details"
                ) from exc
            raise
        return await self._issue(user, "REGISTER", request_id, previous)

    async def login(
        self, data: LoginInput, request_id: str, previous: str | None
    ) -> tuple[User, str]:
        user = await self.repository.user_by_email(str(data.email))
        valid = await to_thread.run_sync(
            verify_password,
            data.password.get_secret_value(),
            user.password_hash if user else DUMMY_HASH,
            limiter=self.limiter,
        )
        if not valid or user is None:
            raise AuthError(401, "INVALID_CREDENTIALS", "Email or password is incorrect")
        return await self._issue(user, "LOGIN", request_id, previous)

    async def _issue(
        self, user: User, action: str, request_id: str, previous: str | None
    ) -> tuple[User, str]:
        if previous:
            await self.repository.delete_session(token_digest(previous))
        token = secrets.token_urlsafe(32)
        session = Session(
            id=uuid4(),
            user_id=user.id,
            token_hash=token_digest(token),
            expires_at=datetime.now(UTC) + timedelta(seconds=self.settings.session_ttl_seconds),
        )
        self.repository.db.add(session)
        self.repository.db.add(
            AuditLog(
                user_id=user.id,
                action=action,
                resource_type="session",
                resource_id=session.id,
                request_id=request_id,
            )
        )
        await self.repository.db.commit()
        await self.repository.db.refresh(user)
        return user, token

    async def authenticate(self, token: str | None) -> tuple[Session, User]:
        if not token or len(token) != 43:
            raise AuthError(401, "UNAUTHENTICATED", "Please sign in to continue")
        result = await self.repository.session_user(token_digest(token))
        if result is None:
            raise AuthError(401, "UNAUTHENTICATED", "Please sign in to continue")
        return result

    async def logout(self, token: str, request_id: str) -> None:
        session, user = await self.authenticate(token)
        await self.repository.delete_session(token_digest(token))
        self.repository.db.add(
            AuditLog(
                user_id=user.id,
                action="LOGOUT",
                resource_type="session",
                resource_id=session.id,
                request_id=request_id,
            )
        )
        await self.repository.db.commit()
