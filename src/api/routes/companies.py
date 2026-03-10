"""Company endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.schemas import (
    CompanyDetail,
    CompanyHistoryOut,
    CompanyOut,
    SnapshotOut,
    TimeseriesPointOut,
)
from src.db.models.warehouse_layer import DimEntity, FactSnapshot, FactTimeseries

router = APIRouter(prefix="/companies", tags=["companies"])


def _resolve_entity_keys(db: Session, company_id: int) -> list[int]:
    """Return all entity_keys for a company name, spanning any metadata changes.

    Raises 404 if the initial company_id does not exist.
    """
    entity = db.query(DimEntity).filter(DimEntity.entity_key == company_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
    return [
        k
        for (k,) in db.query(DimEntity.entity_key)
        .filter(DimEntity.entity_name == entity.entity_name)
        .all()
    ]


@router.get("/compare", response_model=list[SnapshotOut])
async def compare_companies(
    company_ids: str = Query(
        ..., description="Comma-separated entity_key values, e.g. '1,2,3'"
    ),
    as_of_date: str | None = Query(
        None,
        description="ISO-8601 date (YYYY-MM-DD). Returns the latest snapshot "
        "for each company on or before this date. Omit for latest overall.",
    ),
    db: Session = Depends(get_db),
):
    """Compare multiple companies at a specific point in time.

    Example:
        GET /companies/compare?company_ids=1,2&as_of_date=2025-01-01
    """
    try:
        keys = [int(k.strip()) for k in company_ids.split(",")]
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="company_ids must be comma-separated integers",
        )

    cutoff: datetime | None = None
    if as_of_date:
        try:
            cutoff = datetime.fromisoformat(as_of_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format: {as_of_date!r}. Use YYYY-MM-DD.",
            )

    results: list[SnapshotOut] = []
    for key in keys:
        query = (
            db.query(FactSnapshot, DimEntity.entity_name)
            .join(DimEntity, FactSnapshot.entity_key == DimEntity.entity_key)
            .filter(FactSnapshot.entity_key == key, DimEntity.is_current.is_(True))
        )
        if cutoff:
            query = query.filter(FactSnapshot.snapshot_date <= cutoff)
        row = query.order_by(FactSnapshot.snapshot_date.desc()).first()
        if row:
            snap, name = row
            results.append(SnapshotOut.from_row(snap, name))

    return results


@router.get("/", response_model=list[CompanyOut])
async def list_companies(db: Session = Depends(get_db)):
    """List all companies with their current metadata.

    Example:
        GET /companies
    """
    return (
        db.query(DimEntity)
        .filter(DimEntity.is_current.is_(True))
        .order_by(DimEntity.entity_name)
        .all()
    )


@router.get("/{company_id}", response_model=CompanyDetail)
async def get_company(company_id: int, db: Session = Depends(get_db)):
    """Get current company details.

    Example:
        GET /companies/1
    """
    entity = (
        db.query(DimEntity)
        .filter(DimEntity.entity_key == company_id, DimEntity.is_current.is_(True))
        .first()
    )
    if not entity:
        raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
    return entity


@router.get("/{company_id}/versions", response_model=list[SnapshotOut])
async def get_company_versions(company_id: int, db: Session = Depends(get_db)):
    """Get all snapshot versions for a company, ordered chronologically.

    Example:
        GET /companies/1/versions
    """
    entity_keys = _resolve_entity_keys(db, company_id)
    rows = (
        db.query(FactSnapshot, DimEntity.entity_name)
        .join(DimEntity, FactSnapshot.entity_key == DimEntity.entity_key)
        .filter(FactSnapshot.entity_key.in_(entity_keys))
        .order_by(FactSnapshot.version_number)
        .all()
    )
    return [SnapshotOut.from_row(snap, name) for snap, name in rows]


@router.get("/{company_id}/history", response_model=list[CompanyHistoryOut])
async def get_company_history(company_id: int, db: Session = Depends(get_db)):
    """Get time-series data grouped by snapshot version.

    Example:
        GET /companies/1/history
    """
    entity_keys = _resolve_entity_keys(db, company_id)
    snapshots = (
        db.query(FactSnapshot)
        .filter(FactSnapshot.entity_key.in_(entity_keys))
        .order_by(FactSnapshot.version_number)
        .all()
    )

    results: list[CompanyHistoryOut] = []
    for snap in snapshots:
        points = (
            db.query(FactTimeseries)
            .filter(FactTimeseries.snapshot_id == snap.snapshot_id)
            .order_by(FactTimeseries.metric_name, FactTimeseries.year)
            .all()
        )
        results.append(
            CompanyHistoryOut(
                snapshot_id=snap.snapshot_id,
                version_number=snap.version_number,
                snapshot_date=snap.snapshot_date,
                points=[
                    TimeseriesPointOut(
                        metric_name=p.metric_name,
                        year=p.year,
                        is_estimate=p.is_estimate,
                        value=float(p.value) if p.value is not None else None,
                    )
                    for p in points
                ],
            )
        )

    return results
