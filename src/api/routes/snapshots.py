"""Snapshot endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@router.get("/")
async def list_snapshots(
    company_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    sector: str | None = None,
    country: str | None = None,
    currency: str | None = None,
):
    """List company snapshots with optional filters."""
    pass


@router.get("/latest")
async def get_latest_snapshots():
    """Get the latest snapshot for each company."""
    pass


@router.get("/{snapshot_id}")
async def get_snapshot(snapshot_id: int):
    """Get a specific snapshot by ID."""
    pass
