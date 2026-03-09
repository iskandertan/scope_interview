from dataclasses import dataclass
import datetime

from sqlalchemy.orm import Session

from src.db.models.tables import FileMetadata

# TODO: tests for the presence of mandatory fields and their types


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
