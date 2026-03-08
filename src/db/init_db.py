"""Database initialisation entry point.

Calls `create_schemas` then `create_tables` so every schema exists before
SQLAlchemy attempts to create schema-qualified tables.
"""

from sqlalchemy import Engine

from src.db.models.schemas import create_schemas
from src.db.models.tables import create_tables


def init_db(engine: Engine) -> None:
    """Create all schemas and tables; safe to call on every startup."""
    create_schemas(engine)
    create_tables(engine)
