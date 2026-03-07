"""Common dependencies for FastAPI routes."""

from collections.abc import Generator

from src.db.session import SessionLocal


def get_db() -> Generator:
    """Yield a database session, closed after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
