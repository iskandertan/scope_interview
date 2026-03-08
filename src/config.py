"""Application configuration via pydantic-settings."""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/excelsior"
    pipeline_interval: int = 100
    log_level: str = Field(default="info", validation_alias="LOG_LEVEL")
    data_path: Path = Path(__file__).parent.parent / "data"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
