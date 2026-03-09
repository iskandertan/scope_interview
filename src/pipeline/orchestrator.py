"""Pipeline orchestrator - scans data_path and ingests new .xlsm files."""

import logging

from src.config import settings

# from src.db.models.pipeline_state import ProcessedFile
from src.db.session import SessionLocal
from src.pipeline.process_sheet import extract_sheet_data
from src.pipeline.extract_file_metadata import get_metadata
from src.pipeline.load_raw import load_raw_schema


logger = logging.getLogger(__name__)


async def run_pipeline() -> None:
    data_dir = settings.data_path
    # logger.info("Running pipeline.")
    if not data_dir.exists():
        logger.warning("Data directory %s does not exist - skipping run", data_dir)
        return
    for f in data_dir.glob("*.xls*"):
        # Open transaction here
        metadata = get_metadata(f)
        # logger.info(f"{metadata}")
        kv_dict, ts_dict = extract_sheet_data(data_dir / f)
        logger.info(f"{kv_dict}\n{ts_dict}")
        # logger.info(f"{kv_df.shape} {ts_df.shape}")
        # store in raw layer
        # record that this file has been processed
        # commit transaction
    return None


# async def run_pipeline() -> None:
#     """Scan settings.data_path for .xlsm files and ingest any not yet seen.

#     Deduplication is by SHA3-256 content hash — a renamed/moved file that was
#     already ingested is skipped.
#     """
#     data_dir = settings.data_path
#     if not data_dir.exists():
#         logger.warning("Data directory %s does not exist - skipping run", data_dir)
#         return

#     xlsm_files = sorted(data_dir.glob("*.xlsm"))
#     if not xlsm_files:
#         logger.debug("No .xlsm files found in %s", data_dir)
#         return

#     with SessionLocal() as session:
#         for file_path in xlsm_files:
#             try:
#                 file_hash = compute_file_hash(str(file_path))

#                 if session.query(ProcessedFile).filter_by(file_hash=file_hash).first():
#                     logger.debug("Skipping %s - already processed", file_path.name)
#                     continue

#                 logger.info("Processing %s", file_path.name)
#                 stat = file_path.stat()
#                 data = extract_excel(str(file_path))
#                 load_raw_schema(
#                     session, file_hash=file_hash, fname=file_path.name, data=data
#                 )

#                 session.add(
#                     ProcessedFile(
#                         fname=file_path.name,
#                         fpath=str(file_path.resolve()),
#                         file_hash=file_hash,
#                         file_size_bytes=stat.st_size,
#                         file_mtime=datetime.fromtimestamp(
#                             stat.st_mtime, tz=timezone.utc
#                         ),
#                         file_ctime=datetime.fromtimestamp(
#                             stat.st_ctime, tz=timezone.utc
#                         ),
#                     )
#                 )
#                 session.commit()
#                 logger.info("Finished %s", file_path.name)

#             except Exception:
#                 session.rollback()
#                 logger.exception("Failed to process %s", file_path.name)
