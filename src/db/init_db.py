"""Initialize database schemas and tables on startup."""

from sqlalchemy import text

from src.db.models import Base
from src.db.models.pipeline_state import ProcessedFile  # noqa: F401 – registers with Base.metadata
from src.db.models.raw import RawFileUpload, RawSheetRow  # noqa: F401 – registers with Base.metadata


def init_db_schemas(engine):
    """Create schemas and all tables."""
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS warehouse"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS pipeline_state"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
