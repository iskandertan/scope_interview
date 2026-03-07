"""SQLAlchemy models for tracking processed files and pipeline runs."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models import Base


class ProcessedFile(Base):
    """Records every file that has been successfully ingested by the pipeline."""

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
