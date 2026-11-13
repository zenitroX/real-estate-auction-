"""
Configuration and settings management using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable fallback and validation."""

    # Gemini API Settings
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"

    # Supabase Settings
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None

    @property
    def effective_supabase_key(self) -> Optional[str]:
        """Return service role key if available, else standard key."""
        return self.supabase_service_role_key or self.supabase_key

    # Playwright & Scraper Settings
    playwright_headless: bool = True
    rate_limit_requests_per_minute: int = 30
    scrape_state: str = "Tamil Nadu"
    tmp_download_dir: str = "./tmp_notices"
    request_timeout_seconds: float = 30.0

    # Logging & Operation
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def ensure_dirs(self) -> Path:
        """Ensure temporary download directory exists."""
        path = Path(self.tmp_download_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache()
def get_settings() -> Settings:
    """Retrieve and cache settings singleton."""
    return Settings()

