"""Application settings loaded from environment variables."""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    # Database
    DATABASE_URL: str = "sqlite:///./trade_data.db"

    # Data mode
    DATA_MODE: Literal["mock", "live"] = "mock"
    COMTRADE_API_KEY: str = ""
    COMTRADE_BASE_URL: str = "https://comtradeapi.un.org/data/v1"

    # API
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "*"

    # Auth Ã¢â‚¬â€ JWT
    JWT_SECRET: str = "change-me-in-production-please"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 8  # 8h sessions

    # Bootstrap admin
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "changeme"

    # Tier rate limits
    RATE_LIMIT_FREE_PER_DAY: int = 50
    RATE_LIMIT_PAID_PER_DAY: int = 10000
    RATE_LIMIT_STARTER_PER_DAY: int = 500
    RATE_LIMIT_PRO_PER_DAY: int = 10000
    # 'enterprise' is unlimited

    # Razorpay
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    FRONTEND_URL: str = "http://localhost:5173"

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def razorpay_enabled(self) -> bool:
        """True if real Razorpay creds are configured (otherwise mock mode)."""
        return bool(self.RAZORPAY_KEY_ID and self.RAZORPAY_KEY_SECRET)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
