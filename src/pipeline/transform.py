"""Raw -> Warehouse transformer.

Reads raw.sheet rows, validates them via Pydantic, and writes to
warehouse.dim_entity / warehouse.fact_snapshot / warehouse.fact_timeseries.

Pydantic models
    RawAssessment     validated rating assessment (from raw.sheet.key_values)
    IndustryRisk      single industry risk score + weight
    RawTimeseries     single metric x year data point (from raw.sheet.timeseries)

Transformer
    RawToWarehouseTransformer.transform(raw_row, file_meta) -> TransformResult
"""

import logging
import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ValidationError, field_validator, model_validator
from sqlalchemy.orm import Session

from src.db.models.raw_layer import FileMetadataTbl, RawSheetTbl
from src.db.models.warehouse_layer import DimEntity, FactSnapshot, FactTimeseries

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_RATINGS: frozenset[str] = frozenset(
    {
        "AAA",
        "AA+",
        "AA",
        "AA-",
        "A+",
        "A",
        "A-",
        "BBB+",
        "BBB",
        "BBB-",
        "BB+",
        "BB",
        "BB-",
        "B+",
        "B",
        "B-",
        "CCC+",
        "CCC",
        "CCC-",
        "CC",
        "C",
        "D",
    }
)

_NOTCH_RE = re.compile(r"^[+-]\d+ notch(es)?$")

# Maps raw Excel key_values JSON keys -> RawAssessment field names.
# These keys all contain a single value (list of length 1) in the raw data.
_KV_FIELD_MAP: dict[str, str] = {
    "Rated entity": "entity_name",
    "CorporateSector": "corporate_sector",
    "Country of origin": "country",
    "Reporting Currency/Units": "currency",
    "Accounting principles": "accounting_principles",
    "End of business year": "fiscal_year_end_month",
    "Segmentation criteria": "segmentation_criteria",
    "Business risk profile": "business_risk_profile",
    "(Blended) Industry risk profile": "blended_industry_risk_profile",
    "Competitive Positioning": "competitive_positioning",
    "Market share": "market_share",
    "Diversification": "diversification",
    "Operating profitability": "operating_profitability",
    "Sector/company-specific factors (1)": "sector_factor_1",
    "Sector/company-specific factors (2)": "sector_factor_2",
    "Financial risk profile": "financial_risk_profile",
    "Leverage": "leverage",
    "Interest cover": "interest_cover",
    "Cash flow cover": "cash_flow_cover",
    "Liquidity": "liquidity_adjustment",
}

# Fields with multiple values requiring special handling outside of _KV_FIELD_MAP.
_KV_SPECIAL_KEYS = {"Rating methodologies applied", "Industry risk"}


def validate_raw_data(kv: dict) -> None:
    """Raise ValueError if *kv* contains unknown keys or
    fields that fit into _KV_SPECIAL_KEYS but aren't there."""
    unknown = set(kv) - set(_KV_FIELD_MAP) - _KV_SPECIAL_KEYS
    if unknown:
        raise ValueError(f"Unmapped field(s) in raw key_values: {sorted(unknown)}")
    multi = [k for k in kv if k in _KV_FIELD_MAP and len(kv[k]) > 1]
    if multi:
        raise ValueError(
            f"Scalar field(s) with multiple values (add to _KV_SPECIAL_KEYS?): {sorted(multi)}"
        )


# dim_entity metadata fields that trigger a new history record when changed.
_TRACKED_FIELDS = (
    "corporate_sector",
    "country",
    "currency",
    "accounting_principles",
    "fiscal_year_end_month",
)

# FactSnapshot columns that come directly from the assessment.
_SNAPSHOT_FIELDS = (
    "business_risk_profile",
    "blended_industry_risk_profile",
    "competitive_positioning",
    "market_share",
    "diversification",
    "operating_profitability",
    "sector_factor_1",
    "sector_factor_2",
    "financial_risk_profile",
    "leverage",
    "interest_cover",
    "cash_flow_cover",
    "liquidity_adjustment",
    "segmentation_criteria",
)


def _check_rating(v: str | None) -> str:
    if v is not None and v not in VALID_RATINGS:
        raise ValueError(f"Invalid rating: {v!r}")
    return v


# ---------------------------------------------------------------------------
# Pydantic validation models
# ---------------------------------------------------------------------------


class IndustryRisk(BaseModel):
    industry_name: str
    risk_score: str
    weight: float

    @model_validator(mode="before")
    @classmethod
    def strip_whitespace(cls, values: dict) -> dict:
        """Strip leading/trailing whitespace from all string inputs."""
        return {k: v.strip() if isinstance(v, str) else v for k, v in values.items()}

    @field_validator("risk_score")
    @classmethod
    def validate_risk_score(cls, v: str) -> str:
        return _check_rating(v)

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Weight must be between 0 and 1, got {v}")
        return v


class ValidatedAssessment(BaseModel):
    """Validating data from raw.sheet.assessment JSON column."""

    entity_name: str
    corporate_sector: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    accounting_principles: Optional[str] = None
    fiscal_year_end_month: Optional[str] = None
    segmentation_criteria: Optional[str] = None
    rating_methodologies_applied: list[str] = []
    industry_risks: list[IndustryRisk] = []
    # Rating profiles
    business_risk_profile: Optional[str] = None
    blended_industry_risk_profile: Optional[str] = None
    competitive_positioning: Optional[str] = None
    market_share: Optional[str] = None
    diversification: Optional[str] = None
    operating_profitability: Optional[str] = None
    sector_factor_1: Optional[str] = None
    sector_factor_2: Optional[str] = None
    financial_risk_profile: Optional[str] = None
    leverage: Optional[str] = None
    interest_cover: Optional[str] = None
    cash_flow_cover: Optional[str] = None
    liquidity_adjustment: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def strip_whitespace(cls, values: dict) -> dict:
        """Strip leading/trailing whitespace from all string inputs."""
        return {k: v.strip() if isinstance(v, str) else v for k, v in values.items()}

    @field_validator("entity_name", mode="before")
    @classmethod
    def entity_name_not_empty(cls, v: str | None) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("entity_name must not be empty")
        return v

    @field_validator(
        "business_risk_profile",
        "blended_industry_risk_profile",
        "competitive_positioning",
        "market_share",
        "diversification",
        "operating_profitability",
        "sector_factor_1",
        "sector_factor_2",
        "financial_risk_profile",
        "leverage",
        "interest_cover",
        "cash_flow_cover",
    )
    @classmethod
    def validate_rating_field(cls, v: str | None) -> str | None:
        return _check_rating(v)

    @field_validator("liquidity_adjustment")
    @classmethod
    def validate_liquidity(cls, v: str | None) -> str | None:
        if v is not None and not _NOTCH_RE.match(v):
            raise ValueError(f"Invalid liquidity adjustment format: {v!r}")
        return v

    @model_validator(mode="after")
    def validate_weights_sum(self) -> "ValidatedAssessment":
        if self.industry_risks:
            total = sum(r.weight for r in self.industry_risks)
            if not math.isclose(total, 1.0, abs_tol=0.01):
                raise ValueError(f"Industry risk weights must sum to 1.0, got {total}")
        return self

    @classmethod
    def from_raw(cls, kv: dict) -> "ValidatedAssessment":
        """Create an instance of a ValidatedAssessment from raw data.
        The structure of the raw data is validated.
        Field mapping is driven by ``_KV_FIELD_MAP``.
        """

        validate_raw_data(kv)

        # Handling keys with single values
        fields: dict = {
            _KV_FIELD_MAP[excel_key]: raw_list[0] if raw_list else None
            for excel_key, raw_list in kv.items()
            if excel_key in _KV_FIELD_MAP
        }

        # Handling special keys with multiple values
        fields["rating_methodologies_applied"] = [
            s.strip() for s in kv.get("Rating methodologies applied", [])
        ]
        # Industry risks: list of {name: {score, weight}} dicts
        industry_risks = []
        for entry in kv.get("Industry risk", []):
            for name, details in entry.items():
                industry_risks.append(
                    IndustryRisk(
                        industry_name=name,
                        risk_score=details["Industry risk score"],
                        weight=float(details["Industry weight"]),
                    )
                )
        fields["industry_risks"] = industry_risks

        return cls(**fields)


class ValidatedTimeseries(BaseModel):
    """Validating data from raw.sheet.timeseries JSON column."""

    metric_name: str
    year: int
    is_estimate: bool = False

    @field_validator("metric_name", mode="before")
    @classmethod
    def strip_metric_name(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v

    value: Optional[float] = None

    @classmethod
    def from_raw(cls, ts: dict) -> list["ValidatedTimeseries"]:
        """Create an instance of ValidatedTimeseries.
        Expand raw.sheet.timeseries JSON into a flat list of points.
        Year keys ending in 'E' (e.g. "2025E") are flagged as estimates.
        "No data" values become None.
        """
        points = []
        for metric_name, year_values in ts.items():
            for year_key, val in year_values.items():
                year_str = str(year_key)
                is_estimate = year_str.endswith("E")
                year = int(year_str.rstrip("E"))
                value = None if val == "No data" else float(val)
                points.append(
                    cls(
                        metric_name=metric_name,
                        year=year,
                        is_estimate=is_estimate,
                        value=value,
                    )
                )
        return points


# ---------------------------------------------------------------------------
# Transform result
# ---------------------------------------------------------------------------


@dataclass
class TransformResult:
    file_id: int
    success: bool
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Transformer: raw -> warehouse
# ---------------------------------------------------------------------------


class RawToWarehouseTransformer:
    """Validates raw-layer rows via Pydantic and writes to warehouse tables.

    Usage::

        transformer = RawToWarehouseTransformer(session)
        result = transformer.transform(raw_sheet_row, file_metadata_row)
        # caller commits the session
    """

    def __init__(self, session: Session):
        self.session = session

    def transform(
        self, raw: RawSheetTbl, file_meta: FileMetadataTbl
    ) -> TransformResult:
        # Pydantic validations
        try:
            assessment = ValidatedAssessment.from_raw(raw.assessment)
            timeseries = ValidatedTimeseries.from_raw(raw.timeseries)
        except (ValidationError, Exception) as exc:
            logger.warning(f"Validation failed for file_id={raw.file_id}: {exc}")
            return TransformResult(
                file_id=raw.file_id, success=False, errors=[str(exc)]
            )

        entity_key = self._upsert_entity(assessment, file_meta.ctime)
        version = self._next_version(entity_key)

        # Build snapshot from assessment fields + metadata
        snapshot = FactSnapshot(
            entity_key=entity_key,
            file_id=raw.file_id,
            snapshot_date=file_meta.ctime,
            version_number=version,
            rating_methodologies_applied=assessment.rating_methodologies_applied,
            industry_risks=[r.model_dump() for r in assessment.industry_risks],
            **{f: getattr(assessment, f) for f in _SNAPSHOT_FIELDS},
        )
        self.session.add(snapshot)
        self.session.flush()

        for point in timeseries:
            self.session.add(
                FactTimeseries(
                    snapshot_id=snapshot.snapshot_id,
                    entity_key=entity_key,
                    metric_name=point.metric_name,
                    year=point.year,
                    is_estimate=point.is_estimate,
                    value=point.value,
                )
            )

        raw.was_processed = True

        logger.info(
            f"file_id={raw.file_id} -> snapshot_id={snapshot.snapshot_id} "
            f"(entity={assessment.entity_name!r}, v{version}, "
            f"{len(timeseries)} timeseries points)"
        )
        return TransformResult(file_id=raw.file_id, success=True)

    def _upsert_entity(self, assessment: ValidatedAssessment, ctime: datetime) -> int:
        """Insert or update a company in dim_entity, preserving metadata history.

        When tracked metadata changes, the previous record is closed
        (valid_to set, is_current=False) and a new one becomes active.

        Returns the entity_key for the active row.
        """
        current = (
            self.session.query(DimEntity)
            .filter_by(entity_name=assessment.entity_name, is_current=True)
            .first()
        )

        # Nothing changed — reuse existing row
        if current and not self._entity_metadata_differs(current, assessment):
            return current.entity_key

        # Make the previous row obsolete but keep for history
        if current:
            current.valid_to = ctime
            current.is_current = False

        # Insert a new row that becomes the single active version
        entity = DimEntity(
            entity_name=assessment.entity_name,
            valid_from=ctime,
            is_current=True,
            **{f: getattr(assessment, f) for f in _TRACKED_FIELDS},
        )
        self.session.add(entity)
        self.session.flush()
        return entity.entity_key

    @staticmethod
    def _entity_metadata_differs(
        current: DimEntity, assessment: ValidatedAssessment
    ) -> bool:
        """True if any company metadata (sector, country, currency,
        accounting principles, fiscal year-end) differs between the DB row
        and the incoming assessment."""
        return any(getattr(current, f) != getattr(assessment, f) for f in _TRACKED_FIELDS)

    def _next_version(self, entity_key: int) -> int:
        """Return the next snapshot version number for a company.

        Each file upload for the same company produces a new fact_snapshot row
        with an incrementing version (1, 2, 3, ...). This lets us track how
        a company's rating assessment evolved across successive uploads.
        """
        count = (
            self.session.query(FactSnapshot).filter_by(entity_key=entity_key).count()
        )
        return count + 1
