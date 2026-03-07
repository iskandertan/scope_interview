"""SQLAlchemy models for raw schema."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models import Base


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
    """One row per spreadsheet row, per sheet.  All cell values stored as JSONB."""

    __tablename__ = "sheet_rows"
    __table_args__ = {"schema": "raw"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_upload_id: Mapped[int] = mapped_column(
        ForeignKey("raw.file_uploads.id"), nullable=False, index=True
    )
    sheet_name: Mapped[str] = mapped_column(String, nullable=False)
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
