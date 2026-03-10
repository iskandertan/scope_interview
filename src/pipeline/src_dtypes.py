"""Raw-layer ingestion types.

Wraps data extracted from Excel files before inserting into the raw layer tables.
Used in the orchestrator/pipeline to go from: Excel file -> raw.* tables.
"""

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.orm import Session

from src.db.models.raw_layer import FileMetadataTbl, RawSheetTbl


@dataclass(frozen=True)
class SrcFileMetadata:
    fname: str
    ctime: datetime
    sha3_256: str

    def to_orm(self) -> FileMetadataTbl:
        return FileMetadataTbl(
            fname=self.fname, ctime=self.ctime, sha3_256=self.sha3_256
        )

    def existing(self, session: Session) -> FileMetadataTbl | None:
        """Check whether a record with the same sha3_256 already exists."""
        return session.query(FileMetadataTbl).filter_by(sha3_256=self.sha3_256).first()


@dataclass(frozen=True)
class SrcRawExcel:
    key_values: dict
    timeseries: dict
    was_processed: bool = field(default=False)

    def to_orm(self, file_id: int) -> RawSheetTbl:
        return RawSheetTbl(
            file_id=file_id,
            assessment=self.key_values,
            timeseries=self.timeseries,
            was_processed=self.was_processed,
        )
