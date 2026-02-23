"""Application configuration settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # App Info
    APP_NAME: str = "Card Approval API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # MLflow
    MLFLOW_TRACKING_URI: str = "http://127.0.0.1:5000"
    MODEL_NAME: str = "card_approval_model"
    MODEL_STAGE: str = "Production"

    # Model Loading - if MODEL_PATH is set, load from local path (embedded in image)
    # Otherwise, fall back to loading from MLflow at runtime
    MODEL_PATH: str = ""  # e.g., "/app/models" when embedded in Docker image

    # AWS Configuration
    AWS_REGION: str = "ap-southeast-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = "card-approval-prediction-data-production"

    # PostgreSQL Configuration
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "card_approval_api"
    POSTGRES_USER: str = "api_user"
    POSTGRES_PASSWORD: str = ""

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_CACHE_TTL: int = 3600  # 1 hour

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    LOG_FORMAT: str = "text"

    # CORS - comma-separated list of allowed origins (use "*" for development only)
    CORS_ORIGINS: str = "*"

    # OpenTelemetry Tracing
    OTEL_ENABLED: bool = True
    OTEL_SERVICE_NAME: str = "card-approval-api"
    OTEL_EXPORTER_ENDPOINT: str = ""  # e.g., "http://tempo:4317" or "http://tempo.monitoring:4317"
    OTEL_SAMPLING_RATE: float = 1.0  # 1.0 = 100%, 0.1 = 10%

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()
