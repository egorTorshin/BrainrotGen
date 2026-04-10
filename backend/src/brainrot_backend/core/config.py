"""Application settings and configuration helpers."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from brainrot_backend import __version__

Environment = Literal["development", "test", "production"]


class Settings(BaseSettings):
    """Centralized and validated settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="BrainrotGen Backend")
    app_version: str = Field(default=__version__)
    environment: Environment = Field(default="development")
    api_v1_prefix: str = Field(default="/api/v1")
    sqlite_file: str = Field(default="data/app.db")
    database_url: str | None = Field(default=None)

    jwt_secret: str = Field(default="change-me-in-production")
    access_token_expire_minutes: int = Field(default=1440)
    daily_quota_seconds: int = Field(default=300)

    #: Root directory for generated video files (must match worker output mount).
    media_root: Path = Field(default=Path("output"))

    @property
    def resolved_database_url(self) -> str:
        """Return an explicit DB URL or derive one from sqlite_file."""
        if self.database_url:
            return self.database_url
        return f"sqlite+aiosqlite:///./{self.sqlite_file}"

    @property
    def is_development(self) -> bool:
        """Expose environment intent to runtime wiring (logging, debug toggles)."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance for process lifetime."""
    return Settings()
