import datetime
from pathlib import Path
from src.pipeline.data_layers import SrcFileMetadata


def get_sha3_256(file_path: Path) -> str:
    """Compute the SHA3-256 hash of the file at the given path."""
    import hashlib

    if not isinstance(file_path, Path):
        raise ValueError(f"Expected a Path object, got {type(file_path)}")

    hasher = hashlib.sha3_256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_metadata(file_path: Path) -> SrcFileMetadata:
    """Extract filename, UTC creation timestamp (naive), and SHA3-256 hash for the file."""
    if not isinstance(file_path, Path):
        raise ValueError(f"Expected a Path object, got {type(file_path)}")

    ctime_utc_naive = datetime.datetime.fromtimestamp(
        file_path.stat().st_ctime, tz=datetime.timezone.utc
    ).replace(tzinfo=None)

    # TODO: tests for return types
    return SrcFileMetadata(
        fname=file_path.name,
        ctime=ctime_utc_naive,
        sha3_256=get_sha3_256(file_path),
    )
