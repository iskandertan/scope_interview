"""Before any data is stored, every value extracted from the Excel file is validated
against business rules. Invalid data is rejected with a clear error — nothing partial
is ever written to the database.
"""

import pytest
from pydantic import ValidationError

from src.pipeline.transform import (
    IndustryRisk,
    ValidatedAssessment,
    ValidatedTimeseries,
    validate_raw_data,
)

# -- Industry risk ------------------------------------------------------------


class TestIndustryRiskValidation:
    """Each industry exposure entry must have a recognized
    rating and a weight between 0 and 1."""

    def test_entry_is_normalized_on_creation(self):
        """Leading/trailing whitespace in industry names
        and rating codes is stripped."""
        ir = IndustryRisk(industry_name="  Steel  ", risk_score="  BBB ", weight=0.6)
        assert ir.industry_name == "Steel"
        assert ir.risk_score == "BBB"

    def test_unrecognized_rating_code_rejected(self):
        """Only standard credit rating codes (AAA, AA+, BBB-, etc.) are accepted."""
        with pytest.raises(ValidationError, match="Invalid rating"):
            IndustryRisk(industry_name="Steel", risk_score="ZZZ", weight=0.5)

    def test_weight_must_be_between_0_and_1(self):
        with pytest.raises(ValidationError, match="Weight must be between"):
            IndustryRisk(industry_name="Steel", risk_score="BBB", weight=1.5)


# -- Company assessment -------------------------------------------------------


def _minimal_raw_kv(**overrides) -> dict:
    """Minimal raw key-value dict representing a valid
    credit assessment from the spreadsheet."""
    kv = {
        "Rated entity": ["Acme Corp"],
        "Business risk profile": ["BBB+"],
        "Financial risk profile": ["BB"],
        "Leverage": ["BB+"],
        "Interest cover": ["BBB"],
        "Cash flow cover": ["BBB-"],
        "Liquidity": ["+1 notch"],
    }
    kv.update(overrides)
    return kv


class TestAssessmentValidation:
    """Credit assessment data from the Excel file must
    pass all business rules before storage."""

    def test_valid_assessment_is_accepted(self):
        a = ValidatedAssessment.from_raw(_minimal_raw_kv())
        assert a.entity_name == "Acme Corp"
        assert a.business_risk_profile == "BBB+"

    def test_blank_company_name_rejected(self):
        """An assessment without a company name cannot be stored."""
        with pytest.raises(ValidationError, match="entity_name must not be empty"):
            ValidatedAssessment.from_raw(_minimal_raw_kv(**{"Rated entity": [""]}))

    def test_unrecognized_excel_field_rejected(self):
        """Fields that don't map to a known assessment attribute
        are rejected to prevent silent data loss."""
        with pytest.raises(ValueError, match="Unmapped field"):
            validate_raw_data({"Rated entity": ["x"], "Bogus Key": ["y"]})

    def test_company_name_field_must_be_a_single_value(self):
        """Fields like company name that hold one value
        cannot appear multiple times in the sheet."""
        with pytest.raises(ValueError, match="Scalar field"):
            validate_raw_data({"Rated entity": ["Acme", "Other Corp"]})

    def test_unrecognized_rating_code_rejected(self):
        with pytest.raises(ValidationError, match="Invalid rating"):
            ValidatedAssessment.from_raw(
                _minimal_raw_kv(**{"Business risk profile": ["INVALID"]})
            )

    @pytest.mark.parametrize("fmt", ["+1 notch", "-2 notches", "+0 notch"])
    def test_liquidity_adjustment_format(self, fmt):
        """Liquidity adjustments are expressed as signed
        notch counts (e.g. '+1 notch')."""
        a = ValidatedAssessment.from_raw(_minimal_raw_kv(**{"Liquidity": [fmt]}))
        assert a.liquidity_adjustment == fmt

    def test_malformed_liquidity_adjustment_rejected(self):
        with pytest.raises(ValidationError, match="Invalid liquidity adjustment"):
            ValidatedAssessment.from_raw(_minimal_raw_kv(**{"Liquidity": ["bad"]}))

    def test_industry_risk_weights_must_sum_to_one(self):
        """When a company operates in multiple industries,
        the risk weights must sum to 100%."""
        kv = _minimal_raw_kv()
        kv["Industry risk"] = [
            {"Steel": {"Industry risk score": "BBB", "Industry weight": "0.3"}},
            {"Auto": {"Industry risk score": "A", "Industry weight": "0.3"}},
        ]
        with pytest.raises(ValidationError, match="weights must sum to 1.0"):
            ValidatedAssessment.from_raw(kv)

    def test_multi_sector_industry_risk_accepted(self):
        """A company with exposure to multiple industries
        stores each sector individually."""
        kv = _minimal_raw_kv()
        kv["Industry risk"] = [
            {"Steel": {"Industry risk score": "BBB", "Industry weight": "0.6"}},
            {"Auto": {"Industry risk score": "A", "Industry weight": "0.4"}},
        ]
        a = ValidatedAssessment.from_raw(kv)
        assert len(a.industry_risks) == 2
        assert a.industry_risks[0].weight == 0.6

    def test_rating_methodology_names_are_trimmed(self):
        """Methodology names from the spreadsheet are stored
        without leading/trailing whitespace."""
        kv = _minimal_raw_kv()
        kv["Rating methodologies applied"] = ["Method A", " Method B "]
        a = ValidatedAssessment.from_raw(kv)
        assert a.rating_methodologies_applied == ["Method A", "Method B"]


# -- Financial timeseries -----------------------------------------------------


class TestFinancialTimeseriesValidation:
    """Financial history (Revenue, EBITDA, etc.) is extracted as yearly data points."""

    def test_annual_metric_values_are_parsed(self):
        """Each row in the financial history section becomes
        a (metric, year, value) record."""
        points = ValidatedTimeseries.from_raw(
            {"Revenue": {"2022": 100.0, "2023": 200.0}}
        )
        assert len(points) == 2
        assert points[0].metric_name == "Revenue"
        assert points[0].year == 2022
        assert not points[0].is_estimate

    def test_forecast_years_are_flagged_as_estimates(self):
        """Years suffixed with 'E' (e.g. '2025E') are stored with is_estimate=True."""
        points = ValidatedTimeseries.from_raw({"Revenue": {"2025E": 500.0}})
        assert points[0].is_estimate is True
        assert points[0].year == 2025

    def test_missing_data_is_stored_as_null(self):
        """Cells containing 'No data' are stored as NULL rather than a numeric value."""
        points = ValidatedTimeseries.from_raw({"Revenue": {"2022": "No data"}})
        assert points[0].value is None

    def test_multiple_metrics_are_combined_into_one_flat_list(self):
        points = ValidatedTimeseries.from_raw(
            {
                "Revenue": {"2022": 100.0},
                "EBITDA": {"2022": 50.0, "2023E": 60.0},
            }
        )
        assert len(points) == 3
