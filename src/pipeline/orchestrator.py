import logging
from pathlib import Path

from src.config import settings
from src.db.session import SessionLocal
from src.pipeline.process_sheet import extract_sheet_data
from src.pipeline.extract_file_metadata import get_metadata

from src.db.models.tables import RawExcel, FileMetadata

from src.pipeline.source_dtypes import SrcFileMetadata, SrcRawExcel

logger = logging.getLogger(__name__)


async def run_pipeline() -> None:
    data_dir = settings.data_path
    if not data_dir.exists():
        logger.warning("Data directory %s does not exist - skipping run", data_dir)
        return

    for f in data_dir.glob("*.xls*"):  # TODO: any excel file?
        metadata: SrcFileMetadata = get_metadata(f)  # TODO: value of the metadata cls?
        raw_excel: SrcRawExcel = extract_sheet_data(data_dir / f)
        logger.debug(
            f"\nMetadata:\n{metadata}\nKV_DICT:\n{raw_excel.key_values}\nTS_DICT:\n{raw_excel.timeseries}\n"
        )

        populate_raw_layer(metadata, raw_excel, f)

    return None


def populate_raw_layer(metadata: SrcFileMetadata, raw_excel: SrcRawExcel, fpath: Path):
    """Opens a transaction to populate class FileMetadata and class RawExcel tables.
    Rollback on any exception."""
    # TODO: dealing with and detecting rollbacks.
    with SessionLocal.begin() as session:  # TODO: this rollbacks on Exceptions?
        # FileMetadata record
        if metadata.existing(session):
            logger.debug(f"Skipping {fpath.name} - already ingested")
            # TODO: record this for compliance (/uploads) and drop the file
            return
        record: FileMetadata = metadata.to_orm()
        session.add(record)
        session.flush()  # to get record.id for the foreign key in RawExcel
        logger.debug(f"Saved metadata for {fpath.name} (id={record.id})")

        # RawExcel record
        sheet = raw_excel.to_orm(file_id=record.id)
        session.add(sheet)
        logger.debug(f"Saved raw data for {fpath.name} (id={record.id})")
