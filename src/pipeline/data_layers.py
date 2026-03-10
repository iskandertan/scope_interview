"""Data layer types, Pydantic validation models, and transformers.

Bronze source types:
    SrcFileMetadata    wraps file-level metadata before ORM insertion
    SrcRawExcel        wraps raw JSON blobs before ORM insertion

Pydantic validation models:
    IndustryRiskEntry  single industry risk score + weight
    ParsedAssessment   validated rating assessment from raw key_values
    TimeseriesPoint    single metric x year data point

Transformer:
    RawToWarehouseTransformer   bronze -> warehouse (validates via Pydantic)
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

# TODO: tests for the presence of mandatory fields and their types
# TODO: do the data documentation here
# TODO: file name is confusing
from src.db.models.warehouse_layer import DimEntity, FactSnapshot, FactTimeseries

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Valid credit rating values (Scope / S&P scale)
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


def _check_rating(v: str | None) -> str | None:
    if v is not None and v not in VALID_RATINGS:
        raise ValueError(f"Invalid rating: {v!r}")
    return v


def _first_or_none(lst: list) -> str | None:
    return lst[0] if lst else None


# ---------------------------------------------------------------------------
# Raw-layer source dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SrcFileMetadata:
    fname: str
    ctime: datetime
    sha3_256: str

    def to_orm(self) -> FileMetadataTbl:
        return FileMetadataTbl(
            fname=self.fname, ctime=self.ctime, sha3_256=self.sha3_256
        )

    def existing(self, session: Session) -> FileMetadataTbl | None:
        """Check whether a record with the same sha3_256 already exists."""
        return session.query(FileMetadataTbl).filter_by(sha3_256=self.sha3_256).first()


@dataclass(frozen=True)
class SrcRawExcel:
    key_values: dict
    timeseries: dict
    was_processed: bool = field(default=False)

    def to_orm(self, file_id: int) -> RawSheetTbl:
        return RawSheetTbl(
            file_id=file_id,
            key_values=self.key_values,
            timeseries=self.timeseries,
            was_processed=self.was_processed,
        )


# ---------------------------------------------------------------------------
# Pydantic validation models
# ---------------------------------------------------------------------------


class IndustryRiskEntry(BaseModel):
    industry_name: str
    risk_score: str
    weight: float

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


class ParsedAssessment(BaseModel):
    """Validated representation of a rating assessment from raw key_values JSON."""

    # TODO: clarify what's required and what's not?
    entity_name: str
    corporate_sector: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    accounting_principles: Optional[str] = None
    fiscal_year_end_month: Optional[str] = None
    segmentation_criteria: Optional[str] = None
    rating_methodologies_applied: list[str] = []
    industry_risks: list[IndustryRiskEntry] = []
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

    @field_validator("entity_name")
    @classmethod
    def entity_name_not_empty(cls, v: str) -> str:
        v = v.strip()
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
    def validate_weights_sum(self) -> "ParsedAssessment":
        if self.industry_risks:
            total = sum(r.weight for r in self.industry_risks)
            if not math.isclose(total, 1.0, abs_tol=0.01):
                raise ValueError(f"Industry risk weights must sum to 1.0, got {total}")
        return self

    @classmethod
    def from_raw_key_values(cls, kv: dict) -> "ParsedAssessment":
        """Parse raw key_values JSON from raw layer into a validated model."""
        industry_risks = []
        for entry in kv.get("Industry risk", []):
            for name, details in entry.items():
                industry_risks.append(
                    IndustryRiskEntry(
                        industry_name=name,
                        risk_score=details["Industry risk score"],
                        weight=float(details["Industry weight"]),
                    )
                )

        return cls(
            entity_name=_first_or_none(kv.get("Rated entity", [])) or "",
            corporate_sector=_first_or_none(kv.get("CorporateSector", [])),
            country=_first_or_none(kv.get("Country of origin", [])),
            currency=_first_or_none(kv.get("Reporting Currency/Units", [])),
            accounting_principles=_first_or_none(kv.get("Accounting principles", [])),
            fiscal_year_end_month=_first_or_none(kv.get("End of business year", [])),
            segmentation_criteria=_first_or_none(kv.get("Segmentation criteria", [])),
            rating_methodologies_applied=kv.get("Rating methodologies applied", []),
            industry_risks=industry_risks,
            business_risk_profile=_first_or_none(kv.get("Business risk profile", [])),
            blended_industry_risk_profile=_first_or_none(
                kv.get("(Blended) Industry risk profile", [])
            ),
            competitive_positioning=_first_or_none(
                kv.get("Competitive Positioning", [])
            ),
            market_share=_first_or_none(kv.get("Market share", [])),
            diversification=_first_or_none(kv.get("Diversification", [])),
            operating_profitability=_first_or_none(
                kv.get("Operating profitability", [])
            ),
            sector_factor_1=_first_or_none(
                kv.get("Sector/company-specific factors (1)", [])
            ),
            sector_factor_2=_first_or_none(
                kv.get("Sector/company-specific factors (2)", [])
            ),
            financial_risk_profile=_first_or_none(kv.get("Financial risk profile", [])),
            leverage=_first_or_none(kv.get("Leverage", [])),
            interest_cover=_first_or_none(kv.get("Interest cover", [])),
            cash_flow_cover=_first_or_none(kv.get("Cash flow cover", [])),
            liquidity_adjustment=_first_or_none(kv.get("Liquidity", [])),
        )


class TimeseriesPoint(BaseModel):
    """Single metric x year data point parsed from raw timeseries JSON."""

    metric_name: str
    year: int
    is_estimate: bool = False
    value: Optional[float] = None

    @classmethod
    def from_raw_timeseries(cls, ts: dict) -> list["TimeseriesPoint"]:
        """Expand raw timeseries JSON into a flat list of validated points."""
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

_SCD2_FIELDS = (
    "corporate_sector",
    "country",
    "currency",
    "accounting_principles",
    "fiscal_year_end_month",
)


class RawToWarehouseTransformer:
    """Validates raw-layer data via Pydantic and loads into warehouse tables.

    Call ``transform()`` for each unprocessed ``RawExcel`` row.
    The caller is responsible for committing the session.
    """

    def __init__(self, session: Session):
        self.session = session

    def transform(
        self, raw: RawSheetTbl, file_meta: FileMetadataTbl
    ) -> TransformResult:
        # Validate via Pydantic
        try:
            assessment = ParsedAssessment.from_raw_key_values(raw.assessment)
            timeseries = TimeseriesPoint.from_raw_timeseries(raw.timeseries)
        except (ValidationError, Exception) as exc:
            logger.warning(f"Validation failed for file_id={raw.file_id}: {exc}")
            return TransformResult(
                file_id=raw.file_id,
                success=False,
                errors=[str(exc)],
            )

        # SCD2 upsert for dim_entity
        entity_key = self._upsert_entity(assessment, file_meta.ctime)

        # Version number
        version = self._next_version(entity_key)

        # fact_snapshot
        snapshot = FactSnapshot(
            entity_key=entity_key,
            file_id=raw.file_id,
            snapshot_date=file_meta.ctime,
            version_number=version,
            business_risk_profile=assessment.business_risk_profile,
            blended_industry_risk_profile=assessment.blended_industry_risk_profile,
            competitive_positioning=assessment.competitive_positioning,
            market_share=assessment.market_share,
            diversification=assessment.diversification,
            operating_profitability=assessment.operating_profitability,
            sector_factor_1=assessment.sector_factor_1,
            sector_factor_2=assessment.sector_factor_2,
            financial_risk_profile=assessment.financial_risk_profile,
            leverage=assessment.leverage,
            interest_cover=assessment.interest_cover,
            cash_flow_cover=assessment.cash_flow_cover,
            liquidity_adjustment=assessment.liquidity_adjustment,
            segmentation_criteria=assessment.segmentation_criteria,
            rating_methodologies_applied=assessment.rating_methodologies_applied,
            industry_risks=[r.model_dump() for r in assessment.industry_risks],
        )
        self.session.add(snapshot)
        self.session.flush()

        # fact_timeseries
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

        # Mark raw record as processed
        raw.was_processed = True

        logger.info(
            f"Transformed file_id={raw.file_id} -> snapshot_id={snapshot.snapshot_id} "
            f"(entity={assessment.entity_name!r}, v{version}, "
            f"{len(timeseries)} timeseries points)"
        )
        return TransformResult(file_id=raw.file_id, success=True)

    def _upsert_entity(self, assessment: ParsedAssessment, ctime: datetime) -> int:
        """Return entity_key, creating or closing/reopening SCD2 rows as needed."""
        current = (
            self.session.query(DimEntity)
            .filter_by(entity_name=assessment.entity_name, is_current=True)
            .first()
        )

        if current is None:
            entity = DimEntity(
                entity_name=assessment.entity_name,
                corporate_sector=assessment.corporate_sector,
                country=assessment.country,
                currency=assessment.currency,
                accounting_principles=assessment.accounting_principles,
                fiscal_year_end_month=assessment.fiscal_year_end_month,
                valid_from=ctime,
                is_current=True,
            )
            self.session.add(entity)
            self.session.flush()
            return entity.entity_key

        changed = any(
            getattr(current, f) != getattr(assessment, f) for f in _SCD2_FIELDS
        )
        if not changed:
            return current.entity_key

        # Close current version, open new
        current.valid_to = ctime
        current.is_current = False
        new_entity = DimEntity(
            entity_name=assessment.entity_name,
            corporate_sector=assessment.corporate_sector,
            country=assessment.country,
            currency=assessment.currency,
            accounting_principles=assessment.accounting_principles,
            fiscal_year_end_month=assessment.fiscal_year_end_month,
            valid_from=ctime,
            is_current=True,
        )
        self.session.add(new_entity)
        self.session.flush()
        return new_entity.entity_key

    def _next_version(self, entity_key: int) -> int:
        count = (
            self.session.query(FactSnapshot).filter_by(entity_key=entity_key).count()
        )
        return count + 1
