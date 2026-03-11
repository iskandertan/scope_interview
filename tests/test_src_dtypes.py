"""Source dataclass contracts: ORM conversion and immutability."""

from datetime import datetime

import pytest

from src.db.models.raw_layer import FileMetadataTbl, RawSheetTbl
from src.pipeline.src_dtypes import SrcFileMetadata, SrcRawExcel


class TestSrcFileMetadata:
    """SrcFileMetadata wraps file-level metadata extracted before ingestion."""

    def test_to_orm_returns_file_metadata_tbl(self):
        """to_orm returns a FileMetadataTbl ORM instance, not a dict or dataclass."""
        meta = SrcFileMetadata(
            fname="test.xlsm",
            ctime=datetime(2024, 1, 1),
            sha3_256="a" * 64,
        )
        assert isinstance(meta.to_orm(), FileMetadataTbl)

    def test_to_orm_produces_file_metadata_row(self):
        meta = SrcFileMetadata(
            fname="test.xlsm",
            ctime=datetime(2024, 1, 1),
            sha3_256="a" * 64,
        )
        orm = meta.to_orm()
        assert orm.fname == "test.xlsm"
        assert orm.sha3_256 == "a" * 64

    def test_frozen_dataclass_prevents_mutation(self):
        meta = SrcFileMetadata(
            fname="test.xlsm",
            ctime=datetime(2024, 1, 1),
            sha3_256="a" * 64,
        )
        with pytest.raises(AttributeError):
            meta.fname = "changed.xlsm"


class TestSrcRawExcel:
    """SrcRawExcel wraps the key-value and timeseries dicts from a parsed MASTER sheet."""

    def test_to_orm_returns_raw_sheet_tbl(self):
        """to_orm returns a RawSheetTbl ORM instance, not a dict or dataclass."""
        raw = SrcRawExcel(key_values={}, timeseries={})
        assert isinstance(raw.to_orm(file_id=1), RawSheetTbl)

    def test_to_orm_produces_raw_sheet_row(self):
        raw = SrcRawExcel(
            key_values={"Rated entity": ["Acme"]},
            timeseries={"Revenue": {"2022": 100}},
        )
        orm = raw.to_orm(file_id=1)
        assert orm.file_id == 1
        assert orm.assessment == {"Rated entity": ["Acme"]}
        assert orm.timeseries == {"Revenue": {"2022": 100}}
        assert orm.was_processed is False

    def test_frozen_dataclass_prevents_mutation(self):
        raw = SrcRawExcel(key_values={}, timeseries={})
        with pytest.raises(AttributeError):
            raw.key_values = {"new": "data"}
