"""Snapshot endpoints.

Exposes warehouse.fact_snapshot data with filtering, allowing consumers
to query rating assessments across companies, dates, and classifications.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.schemas import SnapshotOut, SnapshotSummary
from src.db.models.warehouse_layer import DimEntity, FactSnapshot

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@router.get("/latest", response_model=list[SnapshotOut])
async def get_latest_snapshots(db: Session = Depends(get_db)):
    """Latest snapshot per company (highest version_number).

    Example:
        GET /snapshots/latest
    """
    latest_sub = (
        db.query(
            FactSnapshot.entity_key,
            func.max(FactSnapshot.version_number).label("max_version"),
        )
        .group_by(FactSnapshot.entity_key)
        .subquery()
    )

    rows = (
        db.query(FactSnapshot, DimEntity.entity_name)
        .join(DimEntity, FactSnapshot.entity_key == DimEntity.entity_key)
        .join(
            latest_sub,
            (FactSnapshot.entity_key == latest_sub.c.entity_key)
            & (FactSnapshot.version_number == latest_sub.c.max_version),
        )
        .order_by(DimEntity.entity_name)
        .all()
    )

    return [SnapshotOut.from_row(snap, name) for snap, name in rows]


@router.get("/", response_model=list[SnapshotSummary])
async def list_snapshots(
    company_id: int | None = Query(None, description="Filter by entity_key"),
    from_date: str | None = Query(
        None, description="Start date (YYYY-MM-DD inclusive)"
    ),
    to_date: str | None = Query(None, description="End date (YYYY-MM-DD inclusive)"),
    sector: str | None = Query(None, description="Filter by corporate sector"),
    country: str | None = Query(None, description="Filter by country"),
    currency: str | None = Query(None, description="Filter by currency"),
    db: Session = Depends(get_db),
):
    """List snapshots with optional filters (all combinable).

    Example:
        GET /snapshots?sector=Corporates&country=Germany&from_date=2024-01-01
    """
    query = db.query(FactSnapshot, DimEntity.entity_name).join(
        DimEntity, FactSnapshot.entity_key == DimEntity.entity_key
    )

    if company_id is not None:
        query = query.filter(FactSnapshot.entity_key == company_id)

    if from_date:
        try:
            dt = datetime.fromisoformat(from_date)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid from_date: {from_date!r}"
            )
        query = query.filter(FactSnapshot.snapshot_date >= dt)

    if to_date:
        try:
            dt = datetime.fromisoformat(to_date)
        except ValueError:
            raise HTTPException(400, detail=f"Invalid to_date: {to_date!r}")
        query = query.filter(FactSnapshot.snapshot_date <= dt)

    if sector:
        query = query.filter(DimEntity.corporate_sector == sector)
    if country:
        query = query.filter(DimEntity.country == country)
    if currency:
        query = query.filter(DimEntity.currency == currency)

    rows = query.order_by(FactSnapshot.snapshot_date.desc()).all()
    return [SnapshotSummary.from_row(snap, name) for snap, name in rows]


@router.get("/{snapshot_id}", response_model=SnapshotOut)
async def get_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    """Full snapshot details by ID.

    Example:
        GET /snapshots/3
    """
    row = (
        db.query(FactSnapshot, DimEntity.entity_name)
        .join(DimEntity, FactSnapshot.entity_key == DimEntity.entity_key)
        .filter(FactSnapshot.snapshot_id == snapshot_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_id} not found")
    snap, entity_name = row
    return SnapshotOut.from_row(snap, entity_name)
