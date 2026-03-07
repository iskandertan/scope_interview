"""Pipeline management endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/trigger")
async def trigger_pipeline():
    """Manually trigger the pipeline."""
    pass


@router.get("/status")
async def get_pipeline_status():
    """Get current pipeline status."""
    pass
