from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "WhatsApp File Pipeline"
    app_env: str = "development"
    log_level: str = "INFO"

    whatsapp_verify_token: SecretStr = SecretStr("")
    whatsapp_access_token: SecretStr = SecretStr("")
    whatsapp_app_secret: SecretStr = SecretStr("")
    whatsapp_phone_number_id: str = ""

    redis_url: str = "redis://redis:6379/0"
    processing_status_ttl_seconds: int = 604800


@lru_cache
def get_settings() -> Settings:
    return Settings()
