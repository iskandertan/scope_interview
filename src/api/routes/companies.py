"""Company endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/")
async def list_companies():
    """List all companies with current metadata."""
    pass


@router.get("/{company_id}")
async def get_company(company_id: int):
    """Get company details (latest version)."""
    pass


@router.get("/{company_id}/versions")
async def get_company_versions(company_id: int):
    """Get all versions for a company."""
    pass


@router.get("/{company_id}/history")
async def get_company_history(company_id: int):
    """Get time-series data for a company."""
    pass


@router.get("/compare")
async def compare_companies(company_ids: str, as_of_date: str | None = None):
    """Compare multiple companies at a specific point in time."""
    pass
