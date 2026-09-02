"""NexusForge application settings — environment-driven, provider-agnostic."""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from .env / environment."""

    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_env: str = Field(default="development")  # development, production, test

    # Application
    max_concurrent_workers: int = Field(default=2, ge=1, le=20)
    default_project_name_format: str = Field(default="{type}-{year}-{number}")

    # Database (default to local Docker services; overridable via .env)
    database_url: str = Field(default="postgresql://postgres:postgres@postgres:5432/nexusforge")
    database_pool_size: int = Field(default=10, ge=1)
    database_max_overflow: int = Field(default=20, ge=0)
    database_pool_timeout: int = Field(default=30, ge=1)

    # Redis (default to local Docker service; overridable via .env)
    redis_url: str = Field(default="redis://redis:6379/0")
    redis_host: str = Field(default="redis")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    redis_password: Optional[str] = None

    # Security
    jwt_secret_key: str = Field(min_length=32)
    jwt_access_token_expire_minutes: int = Field(default=60, ge=1)
    jwt_refresh_token_expire_days: int = Field(default=7, ge=1)
    bcrypt_rounds: int = Field(default=12, ge=4, le=31)
    rate_limit_per_minute: int = Field(default=60, ge=1)
    rate_limit_per_hour: int = Field(default=1000, ge=1)

    # AI Provider — provider-agnostic; no hardcoded provider/model/key
    ai_provider: Optional[str] = None  # openai, anthropic, google, xai, etc.
    ai_model: Optional[str] = None
    ai_api_key: Optional[str] = None  # Never hardcoded; always from env
    ai_max_tokens: int = Field(default=4000, ge=1)
    ai_temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")  # json or detailed
    log_file: Optional[str] = None
    log_timestamp_format: str = Field(default="ISO")

    # Docker / Deployment
    server_host: str = Field(default="0.0.0.0")
    server_port: int = Field(default=8000)

    # Environment
    debug: bool = Field(default=False)
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

    @field_validator('jwt_secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError('JWT_SECRET_KEY must be at least 32 characters')
        return v

    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://')):
            raise ValueError('DATABASE_URL must use postgresql:// scheme')
        return v

    @field_validator('redis_url')
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        if not v.startswith('redis://'):
            raise ValueError('REDIS_URL must use redis:// scheme')
        return v

    @field_validator('api_env')
    @classmethod
    def validate_api_env(cls, v: str) -> str:
        allowed = {'development', 'production', 'testing', 'test'}
        if v not in allowed:
            raise ValueError(f'API_ENV must be one of: {allowed}')
        return v


@lru_cache()
def get_settings() -> Settings:
    return Settings()
