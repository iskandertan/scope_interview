"""Application configuration via pydantic-settings."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/excelsior"
    pipeline_interval: int = 10
    log_level: str = "DEBUG"
    data_path: Path = Path(__file__).parent.parent / "data"

    model_config = {"env_file": ".env"}


settings = Settings()
