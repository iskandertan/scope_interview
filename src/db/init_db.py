"""Initialize database schemas and tables on startup."""

from sqlalchemy import text

from src.db.models import Base


def init_db_schemas(engine):
    """Create schemas and all tables."""
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS warehouse"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS pipeline_state"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
