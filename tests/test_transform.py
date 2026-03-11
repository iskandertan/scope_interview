"""Test the data validation logic that runs when transitioning data from raw into warehouse schema."""

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
    def test_stripped_strings(self):
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
    pass all business rules before being written into a warehouse schema."""

    def test_valid_assessment_is_accepted(self):
        a = ValidatedAssessment.from_raw(_minimal_raw_kv())
        assert a.entity_name == "Acme Corp"
        assert a.business_risk_profile == "BBB+"

    def test_blank_company_name_rejected(self):
        with pytest.raises(ValidationError, match="entity_name must not be empty"):
            ValidatedAssessment.from_raw(_minimal_raw_kv(**{"Rated entity": [""]}))

    def test_unrecognized_excel_field_raises(self):
        """Fields that don't map to a known assessment attribute result in errors."""
        with pytest.raises(ValueError, match="Unmapped field"):
            validate_raw_data({"Rated entity": ["x"], "Bogus Key": ["y"]})

    def test_company_name_field_must_be_a_single_value(self):
        with pytest.raises(ValueError, match="Scalar field"):
            validate_raw_data({"Rated entity": ["Acme", "Other Corp"]})

    def test_unrecognized_rating_code_rejected(self):
        with pytest.raises(ValidationError, match="Invalid rating"):
            ValidatedAssessment.from_raw(
                _minimal_raw_kv(**{"Business risk profile": ["INVALID"]})
            )

    @pytest.mark.parametrize("fmt", ["+1 notch", "-2 notches", "+0 notch"])
    def test_liquidity_adjustment_format(self, fmt):
        a = ValidatedAssessment.from_raw(_minimal_raw_kv(**{"Liquidity": [fmt]}))
        assert a.liquidity_adjustment == fmt

    def test_malformed_liquidity_adjustment_rejected(self):
        with pytest.raises(ValidationError, match="Invalid liquidity adjustment"):
            ValidatedAssessment.from_raw(_minimal_raw_kv(**{"Liquidity": ["bad"]}))

    def test_industry_risk_weights_must_sum_to_one(self):
        kv = _minimal_raw_kv()
        kv["Industry risk"] = [
            {"Steel": {"Industry risk score": "BBB", "Industry weight": "0.3"}},
            {"Auto": {"Industry risk score": "A", "Industry weight": "0.3"}},
        ]
        with pytest.raises(ValidationError, match="weights must sum to 1.0"):
            ValidatedAssessment.from_raw(kv)

    def test_multi_sector_industry_risk_accepted(self):
        kv = _minimal_raw_kv()
        kv["Industry risk"] = [
            {"Steel": {"Industry risk score": "BBB", "Industry weight": "0.6"}},
            {"Auto": {"Industry risk score": "A", "Industry weight": "0.4"}},
        ]
        a = ValidatedAssessment.from_raw(kv)
        assert len(a.industry_risks) == 2
        assert a.industry_risks[0].weight == 0.6

    def test_rating_methodology_names_are_trimmed(self):
        kv = _minimal_raw_kv()
        kv["Rating methodologies applied"] = ["Method A", " Method B "]
        a = ValidatedAssessment.from_raw(kv)
        assert a.rating_methodologies_applied == ["Method A", "Method B"]


# -- Financial timeseries -----------------------------------------------------


class TestFinancialTimeseriesValidation:
    """Financial history (Revenue, EBITDA, etc.) is extracted as yearly data points."""

    def test_annual_metric_values_are_parsed(self):
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
        """Cells containing 'No data' are stored as NULL."""
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
