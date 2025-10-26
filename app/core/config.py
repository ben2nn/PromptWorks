from functools import lru_cache
from typing import Any, Union

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
    BACKEND_CORS_ORIGINS: Union[str, list[str]] = ["http://localhost:5173"]
    BACKEND_CORS_ALLOW_CREDENTIALS: bool = True
    
    # 文件存储配置
    FILE_STORAGE_TYPE: str = "local"  # local, s3, oss
    FILE_STORAGE_PATH: str = "./uploads"
    FILE_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    FILE_BASE_URL: str = "http://localhost:8000"
    
    # 缩略图配置
    THUMBNAIL_SIZE: str = "200x200"
    THUMBNAIL_QUALITY: int = 85
    
    # AWS S3 配置
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_S3_BUCKET: str | None = None
    AWS_S3_REGION: str = "us-east-1"
    
    # 阿里云 OSS 配置
    ALIYUN_ACCESS_KEY_ID: str | None = None
    ALIYUN_ACCESS_KEY_SECRET: str | None = None
    ALIYUN_OSS_BUCKET: str | None = None
    ALIYUN_OSS_ENDPOINT: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # 禁用环境变量的 JSON 解析，让字段验证器处理复杂类型
        env_parse_none_str=None,
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value:
            msg = "DATABASE_URL must be provided"
            raise ValueError(msg)
        return value

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            # 处理逗号分隔的字符串
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, (list, tuple)):
            return [str(origin).strip() for origin in value if str(origin).strip()]
        raise TypeError(
            "BACKEND_CORS_ORIGINS must be a list or a comma separated string"
        )

    @field_validator("FILE_STORAGE_TYPE")
    @classmethod
    def validate_storage_type(cls, value: str) -> str:
        allowed_types = {"local", "s3", "oss"}
        if value not in allowed_types:
            msg = f"FILE_STORAGE_TYPE must be one of {allowed_types}"
            raise ValueError(msg)
        return value

    @field_validator("FILE_MAX_SIZE")
    @classmethod
    def validate_file_max_size(cls, value: int) -> int:
        if value <= 0:
            msg = "FILE_MAX_SIZE must be greater than 0"
            raise ValueError(msg)
        if value > 100 * 1024 * 1024:  # 100MB 上限
            msg = "FILE_MAX_SIZE cannot exceed 100MB"
            raise ValueError(msg)
        return value

    @field_validator("THUMBNAIL_QUALITY")
    @classmethod
    def validate_thumbnail_quality(cls, value: int) -> int:
        if not 1 <= value <= 100:
            msg = "THUMBNAIL_QUALITY must be between 1 and 100"
            raise ValueError(msg)
        return value


@lru_cache
def get_settings() -> Settings:
    """Return a cached application settings instance."""

    return Settings()


settings = get_settings()
