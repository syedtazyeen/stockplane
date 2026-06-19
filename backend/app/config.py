from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Stockplane API"
    debug: bool = False
    api_prefix: str = "/api"

    database_url: str

    secret_key: str = "my-secret-123"
    access_token_expire_minutes: int = 60 * 24
    invite_expire_days: int = 7
    algorithm: str = "HS256"

    db_pool_size: int = 20
    db_max_overflow: int = 30

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    idempotency_ttl_hours: int = 24


@lru_cache
def get_settings() -> Settings:
    return Settings()
