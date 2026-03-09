from dataclasses import dataclass, field
import datetime

from sqlalchemy.orm import Session

from src.db.models.tables import FileMetadata, RawExcel

# TODO: tests for the presence of mandatory fields and their types
# TODO: do the data documentation here


@dataclass(frozen=True)
class SrcFileMetadata:
    fname: str
    ctime: datetime.datetime
    sha3_256: str

    def to_orm(self) -> FileMetadata:
        return FileMetadata(fname=self.fname, ctime=self.ctime, sha3_256=self.sha3_256)

    def existing(self, session: Session) -> FileMetadata | None:
        # TODO: tests here
        """Check whether a record with the same sha3_256 already exists in the database."""
        return session.query(FileMetadata).filter_by(sha3_256=self.sha3_256).first()


@dataclass(frozen=True)
class SrcRawExcel:
    key_values: dict
    timeseries: dict
    was_processed: bool = field(default=False)

    def to_orm(self, file_id) -> RawExcel:
        return RawExcel(
            file_id=file_id,
            key_values=self.key_values,
            timeseries=self.timeseries,
            was_processed=self.was_processed,
        )
