from datetime import datetime

from sqlalchemy.dialects.postgresql import (
    VARCHAR,
    CHAR,
    TIMESTAMP,
    INTEGER,
    JSON,
    BOOLEAN,
)
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base


# ---------------------------------------------------------------------------
# file_uploads schema
# ---------------------------------------------------------------------------


class FileMetadataTbl(Base):
    __tablename__ = "file_metadata"
    __table_args__ = {"schema": "file_uploads"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fname: Mapped[str] = mapped_column(VARCHAR, nullable=False)
    ctime: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), nullable=False)
    sha3_256: Mapped[str] = mapped_column(CHAR(64), nullable=False)


# ---------------------------------------------------------------------------
# raw schema
# ---------------------------------------------------------------------------


class RawSheetTbl(Base):
    __tablename__ = "sheet"
    __table_args__ = {"schema": "raw"}

    file_id: Mapped[int] = mapped_column(
        INTEGER, ForeignKey("file_uploads.file_metadata.id"), primary_key=True
    )
    assessment = mapped_column(JSON, nullable=False)
    timeseries = mapped_column(JSON, nullable=False)
    was_processed = mapped_column(BOOLEAN, nullable=False, default=False)
