"""Warehouse layer (gold) — dimensional model for credit rating analytics.

Following a star schema naming notation.

Tables:
    dim_entity        company dimension with metadata change history
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
# Dimension Tables
# ---------------------------------------------------------------------------


class DimEntity(Base):
    """Tracks changes to company metadata over time."""

    __tablename__ = "dim_entity"
    __table_args__ = {"schema": "warehouse"}

    entity_key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_name: Mapped[str] = mapped_column(VARCHAR, nullable=False)
    corporate_sector: Mapped[Optional[str]] = mapped_column(VARCHAR)
    country: Mapped[Optional[str]] = mapped_column(VARCHAR)
    currency: Mapped[Optional[str]] = mapped_column(VARCHAR(10))
    accounting_principles: Mapped[Optional[str]] = mapped_column(VARCHAR)
    fiscal_year_end_month: Mapped[Optional[str]] = mapped_column(VARCHAR)
    # metadata validity window
    valid_from: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    # valid_to is recorded when a file with new metadata for the same company is ingested
    valid_to: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP) 
    is_current: Mapped[bool] = mapped_column(BOOLEAN, default=True)


# ---------------------------------------------------------------------------
# Facts Tables
# ---------------------------------------------------------------------------


class FactSnapshot(Base):
    """One row per file upload — a complete rating assessment for a company.

    Each upload of an Excel file produces exactly one snapshot. Contains everything
    from the assessment part of the excel sheet - class SrcRawExcel.assessment
    """

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
    # Business risk assessment
    business_risk_profile: Mapped[Optional[str]] = mapped_column(VARCHAR)
    blended_industry_risk_profile: Mapped[Optional[str]] = mapped_column(VARCHAR)
    competitive_positioning: Mapped[Optional[str]] = mapped_column(VARCHAR)
    market_share: Mapped[Optional[str]] = mapped_column(VARCHAR)
    diversification: Mapped[Optional[str]] = mapped_column(VARCHAR)
    operating_profitability: Mapped[Optional[str]] = mapped_column(VARCHAR)
    sector_factor_1: Mapped[Optional[str]] = mapped_column(VARCHAR)
    sector_factor_2: Mapped[Optional[str]] = mapped_column(VARCHAR)
    # Financial risk assessment
    financial_risk_profile: Mapped[Optional[str]] = mapped_column(VARCHAR)
    leverage: Mapped[Optional[str]] = mapped_column(VARCHAR)
    interest_cover: Mapped[Optional[str]] = mapped_column(VARCHAR)
    cash_flow_cover: Mapped[Optional[str]] = mapped_column(VARCHAR)
    liquidity_adjustment: Mapped[Optional[str]] = mapped_column(VARCHAR)
    # Classification
    segmentation_criteria: Mapped[Optional[str]] = mapped_column(VARCHAR)
    rating_methodologies_applied: Mapped[Optional[list]] = mapped_column(JSON)
    industry_risks: Mapped[Optional[list]] = mapped_column(JSON)


class FactTimeseries(Base):
    """One row per metric per year per snapshot."""

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
