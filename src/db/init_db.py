"""Database initialisation entry point.

Calls `create_schemas` then `create_tables` so every schema exists before
SQLAlchemy attempts to create schema-qualified tables.
"""

from sqlalchemy import Engine

from src.db.models.schemas import create_schemas
from src.db.models.bronze_layer import create_bronze_layer
# from src.db.models.silver_layer import create_silver_layer
# from src.db.models.gold_layer import create_gold_layer


def init_db(engine: Engine) -> None:
    """Create all schemas and tables; safe to call on every startup."""
    create_schemas(engine)
    create_bronze_layer(engine)
    # create_silver_layer(engine)
    # create_gold_layer(engine)
