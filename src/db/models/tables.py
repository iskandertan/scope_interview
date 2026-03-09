"""ORM table definitions for all application schemas.

All models are declared here and automatically registered with `Base.metadata`.
`create_tables(engine)` creates every table if it does not already exist.
"""

from datetime import datetime

from sqlalchemy.dialects.postgresql import (
    VARCHAR,
    CHAR,
    TIMESTAMP,
    INTEGER,
    JSON,
    BOOLEAN,
)
from sqlalchemy import Engine, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# file_uploads schema
# ---------------------------------------------------------------------------


class FileMetadata(Base):
    __tablename__ = "file_metadata"
    __table_args__ = {"schema": "file_uploads"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fname: Mapped[str] = mapped_column(VARCHAR, nullable=False)
    ctime: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), nullable=False)
    sha3_256: Mapped[str] = mapped_column(CHAR(64), nullable=False)


# ---------------------------------------------------------------------------
# raw schema
# ---------------------------------------------------------------------------


class RawExcel(Base):
    __tablename__ = "sheet"
    __table_args__ = {"schema": "raw"}

    file_id: Mapped[int] = mapped_column(
        INTEGER, ForeignKey("file_uploads.file_metadata.id"), primary_key=True
    )
    key_values = mapped_column(JSON, nullable=False)
    timeseries = mapped_column(JSON, nullable=False)
    was_processed = mapped_column(BOOLEAN, nullable=False, default=False)


# ---------------------------------------------------------------------------
# Table creation
# ---------------------------------------------------------------------------


def create_tables(engine: Engine) -> None:
    """Create all ORM-mapped tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)
