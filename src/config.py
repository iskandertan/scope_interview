"""Application configuration via pydantic-settings."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    class Config:
        env_file = ".env"


settings = Settings()
