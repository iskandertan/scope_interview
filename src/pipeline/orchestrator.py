import logging
from pathlib import Path

from src.config import settings
from src.db.session import SessionLocal
from src.pipeline.process_sheet import extract_sheet_data
from src.pipeline.extract_file_metadata import get_metadata

from src.db.models.raw_layer import RawSheetTbl, FileMetadataTbl

from src.pipeline.src_dtypes import SrcFileMetadata, SrcRawExcel
from src.pipeline.transform import RawToWarehouseTransformer

logger = logging.getLogger(__name__)


async def run_pipeline() -> None:
    # TODO: document pipeline logic
    data_dir = settings.data_path
    if not data_dir.exists():
        logger.warning("Data directory %s does not exist - skipping run", data_dir)
        return

    # Processing raw data
    for f in data_dir.glob("*.xls*"):  # TODO: any excel file?
        metadata: SrcFileMetadata = get_metadata(f)  # TODO: value of the metadata cls?
        raw_excel: SrcRawExcel = extract_sheet_data(data_dir / f)
        logger.debug(
            f"\nMetadata:\n{metadata}\nKV_DICT:\n{raw_excel.key_values}\nTS_DICT:\n{raw_excel.timeseries}\n"
        )
        populate_raw_layer(metadata, raw_excel, f)

    # Raw -> Warehouse
    populate_warehouse_layer()
    return None


def populate_warehouse_layer():
    with SessionLocal.begin() as session:
        unprocessed = (
            session.query(RawSheetTbl, FileMetadataTbl)
            .join(FileMetadataTbl, RawSheetTbl.file_id == FileMetadataTbl.id)
            .filter(RawSheetTbl.was_processed.is_(False))
            .order_by(FileMetadataTbl.ctime.asc())
            .all()
        )
        if not unprocessed:
            return

        transformer = RawToWarehouseTransformer(session)
        for raw, file_meta in unprocessed:
            result = transformer.transform(raw, file_meta)
            if not result.success:
                logger.error(
                    f"Transform failed for file_id={result.file_id}: {result.errors}"
                )


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
        record: FileMetadataTbl = metadata.to_orm()
        session.add(record)
        session.flush()  # to get record.id for the foreign key in RawExcel
        logger.debug(f"Saved metadata for {fpath.name} (id={record.id})")

        # RawExcel record
        sheet = raw_excel.to_orm(file_id=record.id)
        session.add(sheet)
        logger.debug(f"Saved raw data for {fpath.name} (id={record.id})")
