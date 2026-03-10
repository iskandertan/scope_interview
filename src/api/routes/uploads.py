"""Upload audit endpoints.

Exposes file_uploads.file_metadata and links to warehouse data
so consumers can trace data lineage from source file to snapshot.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.schemas import UploadDetail, UploadOut, UploadStats
from src.config import settings
from src.db.models.raw_layer import FileMetadataTbl
from src.db.models.warehouse_layer import DimEntity, FactSnapshot

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.get("/", response_model=list[UploadOut])
async def list_uploads(db: Session = Depends(get_db)):
    """List all file uploads with metadata.

    Returns every ingested file, most recent first.

    Example:
        GET /uploads
    """
    uploads = db.query(FileMetadataTbl).order_by(FileMetadataTbl.ctime.desc()).all()
    return uploads


@router.get("/stats", response_model=UploadStats)
async def get_upload_stats(db: Session = Depends(get_db)):
    """Upload statistics and metrics.

    Example:
        GET /uploads/stats
    """
    row = db.query(
        func.count(FileMetadataTbl.id),
        func.min(FileMetadataTbl.ctime),
        func.max(FileMetadataTbl.ctime),
    ).first()
    total, earliest, latest = row or (0, None, None)
    return UploadStats(
        total_uploads=total,
        earliest_upload=earliest,
        latest_upload=latest,
    )


@router.get("/{upload_id}", response_model=UploadOut)
async def get_upload(upload_id: int, db: Session = Depends(get_db)):
    """Get metadata for a specific upload.

    Example:
        GET /uploads/1
    """
    upload = db.query(FileMetadataTbl).filter(FileMetadataTbl.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail=f"Upload {upload_id} not found")
    return upload


@router.get("/{upload_id}/details", response_model=UploadDetail)
async def get_upload_details(upload_id: int, db: Session = Depends(get_db)):
    """Get upload with linked snapshot info (data lineage).

    Shows which company and snapshot version a file produced after
    warehouse processing.

    Example:
        GET /uploads/1/details
    """
    upload = db.query(FileMetadataTbl).filter(FileMetadataTbl.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail=f"Upload {upload_id} not found")

    # Look up the snapshot created from this file (if any).
    snap_row = (
        db.query(
            FactSnapshot.snapshot_id, DimEntity.entity_name, FactSnapshot.version_number
        )
        .join(DimEntity, FactSnapshot.entity_key == DimEntity.entity_key)
        .filter(FactSnapshot.file_id == upload_id)
        .first()
    )

    return UploadDetail(
        id=upload.id,
        fname=upload.fname,
        sha3_256=upload.sha3_256,
        ctime=upload.ctime,
        snapshot_id=snap_row[0] if snap_row else None,
        entity_name=snap_row[1] if snap_row else None,
        version_number=snap_row[2] if snap_row else None,
    )


@router.get("/{upload_id}/file")
async def download_upload_file(upload_id: int, db: Session = Depends(get_db)):
    """Download the original uploaded file.

    Resolves the filename from the database and serves it from the
    configured data directory.

    Example:
        GET /uploads/1/file
    """
    upload = db.query(FileMetadataTbl).filter(FileMetadataTbl.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail=f"Upload {upload_id} not found")

    path = settings.data_path / upload.fname
    if not path.is_file():
        raise HTTPException(
            status_code=404, detail=f"File {upload.fname!r} not found on disk"
        )

    return FileResponse(path, filename=upload.fname)
