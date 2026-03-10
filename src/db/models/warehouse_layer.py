"""Warehouse layer (gold) — dimensional model for credit rating analytics.

Tables:
    dim_entity        SCD Type 2 company dimension
    fact_snapshot     One row per rating assessment (per file upload)
    fact_timeseries   One row per metric x year x snapshot
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.dialects.postgresql import (
    VARCHAR,
    TIMESTAMP,
    INTEGER,
    JSON,
    BOOLEAN,
    NUMERIC,
)
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base


# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------


class DimEntity(Base):
    """SCD Type 2 — tracks changes to company metadata over time."""

    __tablename__ = "dim_entity"
    __table_args__ = {"schema": "warehouse"}

    entity_key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_name: Mapped[str] = mapped_column(VARCHAR, nullable=False)
    corporate_sector: Mapped[Optional[str]] = mapped_column(VARCHAR)
    country: Mapped[Optional[str]] = mapped_column(VARCHAR)
    currency: Mapped[Optional[str]] = mapped_column(VARCHAR(10))
    accounting_principles: Mapped[Optional[str]] = mapped_column(VARCHAR)
    fiscal_year_end_month: Mapped[Optional[str]] = mapped_column(VARCHAR)
    # SCD2 tracking
    valid_from: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    valid_to: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    is_current: Mapped[bool] = mapped_column(BOOLEAN, default=True)


# ---------------------------------------------------------------------------
# Facts
# ---------------------------------------------------------------------------


class FactSnapshot(Base):
    """One row per file upload — rating assessment with version tracking."""

    __tablename__ = "fact_snapshot"
    __table_args__ = (
        UniqueConstraint("entity_key", "version_number"),
        {"schema": "warehouse"},
    )

    snapshot_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_key: Mapped[int] = mapped_column(
        INTEGER, ForeignKey("warehouse.dim_entity.entity_key"), nullable=False
    )
    file_id: Mapped[int] = mapped_column(
        INTEGER,
        ForeignKey("file_uploads.file_metadata.id"),
        nullable=False,
        unique=True,
    )
    snapshot_date: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    version_number: Mapped[int] = mapped_column(INTEGER, nullable=False)
    # Rating profiles
    business_risk_profile: Mapped[Optional[str]] = mapped_column(VARCHAR)
    blended_industry_risk_profile: Mapped[Optional[str]] = mapped_column(VARCHAR)
    competitive_positioning: Mapped[Optional[str]] = mapped_column(VARCHAR)
    market_share: Mapped[Optional[str]] = mapped_column(VARCHAR)
    diversification: Mapped[Optional[str]] = mapped_column(VARCHAR)
    operating_profitability: Mapped[Optional[str]] = mapped_column(VARCHAR)
    sector_factor_1: Mapped[Optional[str]] = mapped_column(VARCHAR)
    sector_factor_2: Mapped[Optional[str]] = mapped_column(VARCHAR)
    financial_risk_profile: Mapped[Optional[str]] = mapped_column(VARCHAR)
    leverage: Mapped[Optional[str]] = mapped_column(VARCHAR)
    interest_cover: Mapped[Optional[str]] = mapped_column(VARCHAR)
    cash_flow_cover: Mapped[Optional[str]] = mapped_column(VARCHAR)
    liquidity_adjustment: Mapped[Optional[str]] = mapped_column(VARCHAR)
    segmentation_criteria: Mapped[Optional[str]] = mapped_column(VARCHAR)
    # Stored as JSON — no need for bridge tables at this data volume
    rating_methodologies_applied: Mapped[Optional[list]] = mapped_column(JSON)
    industry_risks: Mapped[Optional[list]] = mapped_column(JSON)


class FactTimeseries(Base):
    """One row per metric x year x snapshot."""

    __tablename__ = "fact_timeseries"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "metric_name", "year"),
        {"schema": "warehouse"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(
        INTEGER,
        ForeignKey("warehouse.fact_snapshot.snapshot_id"),
        nullable=False,
    )
    entity_key: Mapped[int] = mapped_column(
        INTEGER, ForeignKey("warehouse.dim_entity.entity_key"), nullable=False
    )
    metric_name: Mapped[str] = mapped_column(VARCHAR, nullable=False)
    year: Mapped[int] = mapped_column(INTEGER, nullable=False)
    is_estimate: Mapped[bool] = mapped_column(BOOLEAN, default=False)
    value: Mapped[Optional[float]] = mapped_column(NUMERIC)
