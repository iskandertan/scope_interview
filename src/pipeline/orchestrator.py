"""Pipeline orchestrator - scans inbox and processes files."""

import logging
from datetime import datetime, timezone
from pathlib import Path

from src.common.hashing import compute_file_hash
from src.config import settings
from src.db.models.pipeline_state import ProcessedFile
from src.db.session import SessionLocal
from src.pipeline.extract import extract_excel
from src.pipeline.load_raw import load_raw_schema

logger = logging.getLogger(__name__)


async def run_pipeline() -> None:
    """Scan ``settings.data_path`` for .xlsm files and ingest any not yet seen.

    Deduplication is by content hash (SHA3-256): a file that has already been
    recorded in ``pipeline_state.processed_files`` is skipped even if it has
    been renamed or moved.
    """
    data_dir = Path(settings.data_path)
    if not data_dir.exists():
        logger.warning("Data directory %s does not exist – skipping run", data_dir)
        return

    xlsm_files = sorted(data_dir.glob("*.xlsm"))
    if not xlsm_files:
        logger.debug("No .xlsm files found in %s", data_dir)
        return

    with SessionLocal() as session:
        for file_path in xlsm_files:
            try:
                file_hash = compute_file_hash(str(file_path))

                existing = (
                    session.query(ProcessedFile).filter_by(file_hash=file_hash).first()
                )
                if existing:
                    logger.debug(
                        "Skipping %s – already processed (hash=%.16s…)",
                        file_path.name,
                        file_hash,
                    )
                    continue

                logger.info("Processing %s", file_path.name)
                stat = file_path.stat()
                data = extract_excel(str(file_path))
                load_raw_schema(
                    session, file_hash=file_hash, fname=file_path.name, data=data
                )

                session.add(
                    ProcessedFile(
                        fname=file_path.name,
                        fpath=str(file_path.resolve()),
                        file_hash=file_hash,
                        file_size_bytes=stat.st_size,
                        file_mtime=datetime.fromtimestamp(
                            stat.st_mtime, tz=timezone.utc
                        ),
                        file_ctime=datetime.fromtimestamp(
                            stat.st_ctime, tz=timezone.utc
                        ),
                    )
                )
                session.commit()
                logger.info("Finished %s", file_path.name)

            except Exception:
                session.rollback()
                logger.exception("Failed to process %s", file_path.name)
