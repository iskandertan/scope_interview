"""Excel sheet processing: splitting sections and nesting industry risks."""

import pandas as pd
import pytest

from src.pipeline.process_sheet import (
    SPLIT_MARKER,
    get_split_marker_row_index,
    handle_industry_risk_nesting,
    split_dfs,
)


class TestSheetSplitting:
    """The MASTER sheet is split into a key-value/assessment and a timeseries sections.
    This functionality relies on the presence of a SPLIT_MARKER - '[Scope Credit Metrics]'"""

    def test_split_dfs_returns_two_dataframes(self):
        df = pd.DataFrame(
            {0: ["Key", SPLIT_MARKER, "Metric"], 1: ["Val", None, "2022"]}
        )
        result = split_dfs(df, 1)
        assert isinstance(result, tuple) and len(result) == 2
        assert isinstance(result[0], pd.DataFrame)
        assert isinstance(result[1], pd.DataFrame)

    def test_finds_split_marker(self):
        df = pd.DataFrame({0: ["A", "B", SPLIT_MARKER, "D"]})
        assert get_split_marker_row_index(df) == 2

    def test_missing_marker_raises(self):
        df = pd.DataFrame({0: ["A", "B", "C"]})
        with pytest.raises(ValueError, match="Marker.*not found"):
            get_split_marker_row_index(df)

    def test_drop_column_when_all_locked(self):
        df = pd.DataFrame(
            {
                0: ["Key", SPLIT_MARKER, "Metric", "Revenue"],
                1: ["Val", "2022", 200, 100],
                2: ["Other", "Status", "Locked", "Locked"],
            }
        )
        _, df_ts = split_dfs(df, 1)
        assert "Status" not in df_ts.columns


class TestIndustryRiskNesting:
    """
    Industry risk is supposed to be nested like
    "Industry risk": [
        {"Automotive Suppliers": {"Industry risk score": "BBB", "Industry weight": "0.25"}}, 
        {"Automotive and Commercial Vehicle Manufacturers": {"Industry risk score": "BB", "Industry weight": "0.75"}}
        ],
    """

    def test_handle_industry_risk_nesting_returns_dict(self):
        """handle_industry_risk_nesting always returns a dict regardless of input."""
        kv = {"Rated entity": ["Acme"]}
        assert isinstance(handle_industry_risk_nesting(kv), dict)

    def test_nests_scores_and_weights_under_industry_name(self):
        """Flat risk fields are restructured into a list of {name: {score, weight}}."""
        kv = {
            "Something": ["x"],
            "Industry Risk": ["Steel", "Auto"],
            "Industry risk score": ["BBB", "A"],
            "Industry weight": ["0.6", "0.4"],
            "Segmentation criteria": ["Corporate"],
        }
        result = handle_industry_risk_nesting(kv)

        risks = result["Industry Risk"]
        assert len(risks) == 2
        # score and weight are nested for both industries
        assert risks[0]["Steel"]["Industry risk score"] == "BBB"
        assert risks[0]["Steel"]["Industry weight"] == "0.6"
        assert risks[1]["Auto"]["Industry risk score"] == "A"
        assert risks[1]["Auto"]["Industry weight"] == "0.4"
        # flat keys are removed; boundary key is preserved
        assert "Industry risk score" not in result
        assert "Industry weight" not in result
        assert "Segmentation criteria" in result

    def test_no_industry_risk_leaves_data_unchanged(self):
        """KV data without industry risk fields passes through unmodified."""
        kv = {"Rated entity": ["Acme"], "Segmentation criteria": ["Corporate"]}
        result = handle_industry_risk_nesting(kv)
        assert result == kv
