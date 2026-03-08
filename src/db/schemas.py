"""PostgreSQL schema definitions.

All application schemas are declared here. `create_schemas` is called at
startup before any table DDL so SQLAlchemy can resolve schema-qualified names.
"""

from sqlalchemy import Engine
from sqlalchemy.schema import CreateSchema

SCHEMAS: list[str] = [
    "raw",
    "warehouse",
    "pipeline_state",
]


def create_schemas(engine: Engine) -> None:
    """Create all application schemas if they do not already exist."""
    with engine.begin() as conn:
        for schema in SCHEMAS:
            conn.execute(CreateSchema(schema, if_not_exists=True))
