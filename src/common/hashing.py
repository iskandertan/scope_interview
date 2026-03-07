"""File content hashing for deduplication."""

import hashlib


def compute_file_hash(file_path: str) -> str:
    """Compute SHA3-256 hash of file content (streaming, 64 KiB chunks)."""
    h = hashlib.sha3_256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
