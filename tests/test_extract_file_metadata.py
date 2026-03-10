"""Uploaded files are fingerprinted for deduplication and audit."""

from datetime import datetime

import pytest

from src.pipeline.extract_file_metadata import get_metadata, get_sha3_256


class TestUploadedFileIngestion:
    def test_uploaded_file_is_fingerprinted_for_deduplication(self, tmp_path):
        """Each file receives a SHA3-256 fingerprint so
        re-uploads of the same file can be detected."""
        f = tmp_path / "data.xlsm"
        f.write_bytes(b"xlsx data")
        fingerprint = get_sha3_256(f)

        assert len(fingerprint) == 64
        assert fingerprint == get_sha3_256(f)  # same file always yields the same hash

    def test_file_metadata_captures_name_and_timestamp(self, tmp_path):
        """On upload, the app records the filename and the file's creation time."""
        f = tmp_path / "data.xlsm"
        f.write_bytes(b"xlsx data")
        meta = get_metadata(f)

        assert meta.fname == "data.xlsm"
        assert isinstance(meta.ctime, datetime)
        assert len(meta.sha3_256) == 64

    def test_file_path_must_be_provided_as_path_object(self):
        """Raw string paths are rejected — callers must resolve the file path first."""
        with pytest.raises(ValueError, match="Expected a Path"):
            get_metadata("/some/string/path")  # type: ignore
