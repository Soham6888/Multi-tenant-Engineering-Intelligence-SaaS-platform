from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EIP_", env_file=".env", extra="ignore")

    database_url: SecretStr = SecretStr(
        "postgresql+asyncpg://eip:local-development-only@localhost:5432/eip"
    )
    redis_url: SecretStr = SecretStr("redis://localhost:6379/0")
    environment: Literal["local", "production"] = "local"
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    session_ttl_seconds: int = Field(default=43200, ge=300, le=604800)
    auth_ip_limit: int = Field(default=30, ge=1)
    auth_account_limit: int = Field(default=10, ge=1)
    auth_window_seconds: int = Field(default=300, ge=1)
    password_hash_concurrency: int = Field(default=2, ge=1, le=8)

    @property
    def cookie_name(self) -> str:
        return "__Host-eip_session" if self.environment == "production" else "eip_session"

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        if not self.allowed_origins or any(
            not origin.startswith(("http://", "https://")) or origin.endswith("/")
            for origin in self.allowed_origins
        ):
            raise ValueError("Configure explicit origins without trailing slashes")
        if self.environment == "production" and any(
            not origin.startswith("https://") for origin in self.allowed_origins
        ):
            raise ValueError("Production origins must use HTTPS")
        return self
