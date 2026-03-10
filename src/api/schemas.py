"""Pydantic response schemas for the REST API.
Grouped by their corresponding endpoints."""

from datetime import datetime

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# /companies
# ---------------------------------------------------------------------------


class CompanyOut(BaseModel):
    """Current company metadata."""

    entity_key: int
    entity_name: str
    corporate_sector: str | None = None
    country: str | None = None
    currency: str | None = None
    accounting_principles: str | None = None
    fiscal_year_end_month: str | None = None
    valid_from: datetime

    model_config = {"from_attributes": True}


class CompanyDetail(CompanyOut):
    """Company record including validity window (when this version was active)."""

    valid_to: datetime | None = None
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
    business_risk_profile: str | None = None
    blended_industry_risk_profile: str | None = None
    competitive_positioning: str | None = None
    market_share: str | None = None
    diversification: str | None = None
    operating_profitability: str | None = None
    sector_factor_1: str | None = None
    sector_factor_2: str | None = None
    # Financial risk
    financial_risk_profile: str | None = None
    leverage: str | None = None
    interest_cover: str | None = None
    cash_flow_cover: str | None = None
    liquidity_adjustment: str | None = None
    # Classification
    segmentation_criteria: str | None = None
    rating_methodologies_applied: list[str] | None = None
    industry_risks: list[IndustryRiskOut] | None = None

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
    business_risk_profile: str | None = None
    financial_risk_profile: str | None = None

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
    value: float | None = None

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

    snapshot_id: int | None = None
    entity_name: str | None = None
    version_number: int | None = None


class UploadStats(BaseModel):
    """Aggregate upload statistics."""

    total_uploads: int
    earliest_upload: datetime | None = None
    latest_upload: datetime | None = None
