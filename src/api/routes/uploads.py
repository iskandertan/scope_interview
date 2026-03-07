"""Upload audit endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.db.models.raw import RawFileUpload

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.get("/")
async def list_uploads(db: Session = Depends(get_db)):
    """List all file uploads with metadata."""
    uploads = db.query(RawFileUpload).order_by(RawFileUpload.ingested_at.desc()).all()
    return [
        {
            "id": u.id,
            "fname": u.fname,
            "file_hash": u.file_hash,
            "ingested_at": u.ingested_at,
        }
        for u in uploads
    ]


@router.get("/stats")
async def get_upload_stats(db: Session = Depends(get_db)):
    """Upload statistics and metrics."""
    total = db.query(RawFileUpload).count()
    return {"total_uploads": total}


@router.get("/{upload_id}")
async def get_upload(upload_id: int, db: Session = Depends(get_db)):
    """Get details for a specific upload."""
    upload = db.query(RawFileUpload).filter(RawFileUpload.id == upload_id).first()
    if not upload:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Upload not found")
    return {
        "id": upload.id,
        "fname": upload.fname,
        "file_hash": upload.file_hash,
        "ingested_at": upload.ingested_at,
    }
