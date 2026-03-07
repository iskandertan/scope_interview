"""Quality report endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/quality-reports", tags=["quality"])


@router.get("/")
async def get_quality_reports():
    """Get quality reports."""
    pass
