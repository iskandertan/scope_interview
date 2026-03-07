"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/interview"
    pipeline_interval: int = 30
    log_level: str = "DEBUG"

    model_config = {"env_file": ".env"}


settings = Settings()
