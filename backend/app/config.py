from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"


class Settings(BaseSettings):
    """Validated application settings loaded from environment variables."""

    app_name: str = "ResolveAI"
    app_version: str = "0.1.0"
    app_env: Literal[
        "development",
        "test",
        "production",
    ] = "development"

    debug: bool = True
    api_prefix: str = "/api"

    database_url: str = (
        f"sqlite:///{(DATA_DIR / 'resolve_ai.db').as_posix()}"
    )

    frontend_origin: str = "http://localhost:5173"

    # Language-model configuration
    llm_provider: Literal[
        "openai",
        "deterministic",
    ] = "deterministic"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # Maximum retries after the initial tool attempt
    max_tool_retries: int = 2

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Create and cache one settings object for the application."""

    return Settings()


settings = get_settings()