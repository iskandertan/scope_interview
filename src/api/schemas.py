"""Pydantic response schemas for the REST API.
Grouped by their corresponding endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# /companies
# ---------------------------------------------------------------------------


class CompanyOut(BaseModel):
    """Current company metadata."""

    entity_key: int
    entity_name: str
    corporate_sector: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    accounting_principles: Optional[str] = None
    fiscal_year_end_month: Optional[str] = None
    valid_from: datetime

    model_config = {"from_attributes": True}


class CompanyDetail(CompanyOut):
    """Company record including validity window (when this version was active)."""

    valid_to: Optional[datetime] = None
    is_current: bool


# ---------------------------------------------------------------------------
# /snapshots
# ---------------------------------------------------------------------------


class IndustryRiskOut(BaseModel):
    """Sub-model for industry risk entries within a snapshot."""

    industry_name: str
    risk_score: str
    weight: float


class SnapshotOut(BaseModel):
    """Full snapshot — one per file upload / rating assessment."""

    snapshot_id: int
    entity_key: int
    entity_name: str
    file_id: int
    snapshot_date: datetime
    version_number: int
    # Business risk
    business_risk_profile: Optional[str] = None
    blended_industry_risk_profile: Optional[str] = None
    competitive_positioning: Optional[str] = None
    market_share: Optional[str] = None
    diversification: Optional[str] = None
    operating_profitability: Optional[str] = None
    sector_factor_1: Optional[str] = None
    sector_factor_2: Optional[str] = None
    # Financial risk
    financial_risk_profile: Optional[str] = None
    leverage: Optional[str] = None
    interest_cover: Optional[str] = None
    cash_flow_cover: Optional[str] = None
    liquidity_adjustment: Optional[str] = None
    # Classification
    segmentation_criteria: Optional[str] = None
    rating_methodologies_applied: Optional[list[str]] = None
    industry_risks: Optional[list[IndustryRiskOut]] = None

    @classmethod
    def from_row(cls, snap: object, entity_name: str) -> "SnapshotOut":
        """Build from a FactSnapshot ORM row + entity_name (not on the ORM)."""
        data = {k: v for k, v in snap.__dict__.items() if not k.startswith("_")}
        data["entity_name"] = entity_name
        return cls.model_validate(data)


class SnapshotSummary(BaseModel):
    """Lightweight snapshot for list views."""

    snapshot_id: int
    entity_key: int
    entity_name: str
    file_id: int
    snapshot_date: datetime
    version_number: int
    business_risk_profile: Optional[str] = None
    financial_risk_profile: Optional[str] = None

    @classmethod
    def from_row(cls, snap: object, entity_name: str) -> "SnapshotSummary":
        """Build from a FactSnapshot ORM row + entity_name."""
        data = {k: v for k, v in snap.__dict__.items() if not k.startswith("_")}
        data["entity_name"] = entity_name
        return cls.model_validate(data)


# ---------------------------------------------------------------------------
# /companies/{id}/history
# ---------------------------------------------------------------------------


class TimeseriesPointOut(BaseModel):
    """Single metric x year data point."""

    metric_name: str
    year: int
    is_estimate: bool
    value: Optional[float] = None

    model_config = {"from_attributes": True}


class CompanyHistoryOut(BaseModel):
    """Time-series data grouped by snapshot version."""

    snapshot_id: int
    version_number: int
    snapshot_date: datetime
    points: list[TimeseriesPointOut]


# ---------------------------------------------------------------------------
# /uploads
# ---------------------------------------------------------------------------


class UploadOut(BaseModel):
    """File upload metadata."""

    id: int
    fname: str
    sha3_256: str
    ctime: datetime

    model_config = {"from_attributes": True}


class UploadDetail(UploadOut):
    """Upload with linked snapshot info (if warehouse processing completed)."""

    snapshot_id: Optional[int] = None
    entity_name: Optional[str] = None
    version_number: Optional[int] = None


class UploadStats(BaseModel):
    """Aggregate upload statistics."""

    total_uploads: int
    earliest_upload: Optional[datetime] = None
    latest_upload: Optional[datetime] = None
