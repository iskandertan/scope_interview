import datetime
from pathlib import Path


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


def get_metadata(file_path: Path) -> dict:
    """Extract filename and creation time metadata from the given file path."""
    if not isinstance(file_path, Path):
        raise ValueError(f"Expected a Path object, got {type(file_path)}")

    stat = file_path.stat()
    metadata = {
        "fname": file_path.name,
        "file_ctime": datetime.datetime.fromtimestamp(
            stat.st_ctime, tz=datetime.timezone.utc
        ),
        "hash": get_sha3_256(file_path),
    }
    return metadata
