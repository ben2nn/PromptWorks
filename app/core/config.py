from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    APP_ENV: str = "development"
    # 是否启用测试模式，用于控制 DEBUG 级别日志的输出
    APP_TEST_MODE: bool = False
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "PromptWorks"
    DATABASE_URL: str = (
        "postgresql+psycopg://promptworks:promptworks@localhost:5432/promptworks"
    )
    REDIS_URL: str = "redis://localhost:6379/0"
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value:
            msg = "DATABASE_URL must be provided"
            raise ValueError(msg)
        return value


@lru_cache
def get_settings() -> Settings:
    """Return a cached application settings instance."""

    return Settings()


settings = get_settings()
