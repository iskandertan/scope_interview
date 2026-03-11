from datetime import datetime

import pytest

from src.pipeline.extract_file_metadata import get_metadata, get_sha3_256
from src.pipeline.src_dtypes import SrcFileMetadata


class TestExtractingFileMetadata:
    def test_get_metadata_returns_src_file_metadata(self, tmp_path):
        f = tmp_path / "data.xlsm"
        f.write_bytes(b"xlsx data")
        assert isinstance(get_metadata(f), SrcFileMetadata)

    def tests_duplicate_files_same_hash(self, tmp_path):
        f = tmp_path / "data.xlsm"
        f.write_bytes(b"xlsx data")
        fingerprint = get_sha3_256(f)

        assert len(fingerprint) == 64
        assert fingerprint == get_sha3_256(f)

    def test_file_metadata_captures_name_and_timestamp(self, tmp_path):
        f = tmp_path / "data.xlsm"
        f.write_bytes(b"xlsx data")
        meta = get_metadata(f)

        assert meta.fname == "data.xlsm"
        assert isinstance(meta.ctime, datetime)
        assert len(meta.sha3_256) == 64

    def test_file_path_must_be_provided_as_path_object(self):
        with pytest.raises(ValueError, match="Expected a Path"):
            get_metadata("/some/string/path")  # type: ignore
