"""ORM table definitions for all application schemas.

All models are declared here and automatically registered with `Base.metadata`.
`create_tables(engine)` creates every table if it does not already exist.
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy import Engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# raw schema
# ---------------------------------------------------------------------------


class RawFileUpload(Base):
    """One row per ingested file; acts as the parent for raw sheet rows."""

    __tablename__ = "file_uploads"
    __table_args__ = {"schema": "raw"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fname: Mapped[str] = mapped_column(String, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RawSheetRow(Base):
    """One row per spreadsheet row, per sheet. All cell values stored as JSONB."""

    __tablename__ = "sheet_rows"
    __table_args__ = {"schema": "raw"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_upload_id: Mapped[int] = mapped_column(
        ForeignKey("raw.file_uploads.id"), nullable=False, index=True
    )
    sheet_name: Mapped[str] = mapped_column(String, nullable=False)
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)


# ---------------------------------------------------------------------------
# pipeline_state schema
# ---------------------------------------------------------------------------


class ProcessedFile(Base):
    """Records every file successfully ingested; keyed by content hash for deduplication."""

    __tablename__ = "processed_files"
    __table_args__ = {"schema": "pipeline_state"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fname: Mapped[str] = mapped_column(String, nullable=False)
    fpath: Mapped[str] = mapped_column(String, nullable=False)
    file_hash: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, index=True
    )
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    file_mtime: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    file_ctime: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ---------------------------------------------------------------------------
# Table creation
# ---------------------------------------------------------------------------


def create_tables(engine: Engine) -> None:
    """Create all ORM-mapped tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)
