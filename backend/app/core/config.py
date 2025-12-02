"""Application configuration settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "ML-Server-Manager"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./mlsmanager.db"

    # Security
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    algorithm: str = "HS256"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Data Storage
    data_dir: str = "./data"  # Directory for storing logs, outputs, etc.

    # Node Configuration
    node_type: Literal["master", "worker"] = "master"
    node_id: str = "master-001"
    master_url: str | None = None  # Required for worker nodes

    # RabbitMQ (for Celery task queue)
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672//"
    celery_result_backend: str = "rpc://"

    # Default Admin User (for development/initial setup)
    default_admin_username: str = "mlsmanager"
    default_admin_email: str = "admin@mlsmanager.dev"
    default_admin_password: str = "mlsmanager_secret"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
