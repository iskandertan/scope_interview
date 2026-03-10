"""Database initialisation entry point.

Calls ``create_schemas`` then ``Base.metadata.create_all`` so every schema
exists before SQLAlchemy attempts to create schema-qualified tables.
"""

from sqlalchemy import Engine

from src.db.models.schemas import create_schemas
from src.db.models.base import Base

# Import model modules so their tables register with Base.metadata
from src.db.models.raw_layer import FileMetadataTbl, RawSheetTbl  # noqa: F401
from src.db.models.warehouse_layer import DimEntity, FactSnapshot, FactTimeseries  # noqa: F401


def init_db(engine: Engine) -> None:
    """Create all schemas and tables; safe to call on every startup."""
    create_schemas(engine)
    Base.metadata.create_all(bind=engine)
