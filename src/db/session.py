"""Database session and engine configuration."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Create engine and SessionLocal (to be configured with DB URL from settings)
engine = None
SessionLocal = None


def init_db(database_url: str):
    """Initialize database engine and session factory."""
    global engine, SessionLocal
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
