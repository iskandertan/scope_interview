"""Load extracted data into raw schema tables."""

from sqlalchemy.orm import Session

from src.db.models.tables import RawFileUpload, RawSheetRow


def load_raw_schema(
    session: Session, file_hash: str, fname: str, data: dict[str, list[dict]]
) -> None:
    """Insert all sheet rows from *data* into the raw schema.

    Creates one ``RawFileUpload`` record then bulk-inserts one ``RawSheetRow``
    per spreadsheet row.  The *session* is **not** committed here; the caller
    owns the transaction boundary.
    """
    upload = RawFileUpload(file_hash=file_hash, fname=fname)
    session.add(upload)
    session.flush()  # populate upload.id before inserting children

    rows: list[RawSheetRow] = []
    for sheet_name, sheet_rows in data.items():
        for row_index, row_data in enumerate(sheet_rows):
            rows.append(
                RawSheetRow(
                    file_upload_id=upload.id,
                    sheet_name=sheet_name,
                    row_index=row_index,
                    data=row_data,
                )
            )

    if rows:
        session.bulk_save_objects(rows)
