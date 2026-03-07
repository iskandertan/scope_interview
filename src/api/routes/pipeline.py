"""Pipeline management endpoints."""

import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.db.models.pipeline_state import ProcessedFile
from src.pipeline.orchestrator import run_pipeline

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/trigger", status_code=202)
async def trigger_pipeline():
    """Manually trigger a pipeline run in the background."""
    asyncio.create_task(run_pipeline())
    return {"status": "accepted"}


@router.get("/status")
async def get_pipeline_status(db: Session = Depends(get_db)):
    """Return count of files processed by the pipeline."""
    count = db.query(ProcessedFile).count()
    return {"processed_files": count}
