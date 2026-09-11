"""
API Service — Core Settings Configuration
Loaded from environment variables via pydantic-settings.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Service ──
    service_name: str = "api-service"
    environment: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    api_reload: bool = False
    version: str = "0.1.0"

    # ── PostgreSQL ──
    database_url: str = "postgresql+asyncpg://app_user:password@postgres:5432/scalable_ai"
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_recycle: int = 1800  # seconds
    db_pool_timeout: int = 30
    db_echo: bool = False

    # ── MongoDB ──
    mongo_url: str = (
        "mongodb://app_user:password@mongo:27017/scalable_ai_docs?authSource=scalable_ai_docs"
    )
    mongo_db: str = "scalable_ai_docs"
    mongo_max_pool_size: int = 50
    mongo_min_pool_size: int = 10

    # ── Redis ──
    redis_url: str = "redis://redis:6379/0"
    redis_max_connections: int = 50

    # ── Auth ──
    jwt_secret_key: str = "CHANGE_ME_jwt_secret_minimum_32_chars"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # ── CORS ──
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def json_logs(self) -> bool:
        return not self.is_development


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
