"""Application configuration loaded from environment variables / .env file."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "PocketSmart AI"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    DATABASE_URL: str = "sqlite:///./pocketsmart.db"

    # Google Gemini (optional - demo mode when empty)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CONTINGENCY_PERCENT: float = 10.0
    ALLOWED_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000"
    MAX_UPLOAD_SIZE_MB: int = 5
    UPLOAD_DIR: str = "app/static/uploads"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
