"""Excel sheet processing: splitting sections and nesting industry risks."""

import pytest
import pandas as pd

from src.pipeline.process_sheet import (
    get_split_marker_row_index,
    handle_industry_risk_nesting,
    split_dfs,
    SPLIT_MARKER,
)


class TestSheetSplitting:
    """The MASTER sheet is split into a key-value section and a timeseries section."""

    def test_finds_split_marker(self):
        """The marker row separating KV from timeseries data is located correctly."""
        df = pd.DataFrame({0: ["A", "B", SPLIT_MARKER, "D"]})
        assert get_split_marker_row_index(df) == 2

    def test_missing_marker_raises(self):
        """Sheets without a split marker are rejected."""
        df = pd.DataFrame({0: ["A", "B", "C"]})
        with pytest.raises(ValueError, match="Marker.*not found"):
            get_split_marker_row_index(df)

    def test_splits_into_kv_and_timeseries(self):
        """Rows above the marker become key-value pairs; rows below become timeseries."""
        df = pd.DataFrame(
            {
                0: ["Key1", "Key2", SPLIT_MARKER, "Metric", "Revenue"],
                1: ["Val1", "Val2", None, "2022", 100],
                2: [None, None, None, "2023", 200],
            }
        )
        df_kv, df_ts = split_dfs(df, 2)

        assert len(df_kv) == 2
        assert df_kv.iloc[0, 0] == "Key1"
        assert len(df_ts) == 2
        assert df_ts.iloc[0, 0] == "Metric"

    def test_locked_status_column_is_dropped(self):
        """Columns containing 'Locked'/'Status' metadata are removed from timeseries."""
        df = pd.DataFrame(
            {
                0: [SPLIT_MARKER, "Metric", "Revenue"],
                1: [None, "2022", 100],
                2: [None, "Status", "Locked"],
            }
        )
        _, df_ts = split_dfs(df, 0)
        assert "Status" not in df_ts.columns


class TestIndustryRiskNesting:
    """Industry risk scores and weights are nested under each industry name."""

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
        assert risks[0]["Steel"]["Industry risk score"] == "BBB"
        assert "Industry risk score" not in result
        assert "Industry weight" not in result

    def test_no_industry_risk_leaves_data_unchanged(self):
        """KV data without industry risk fields passes through unmodified."""
        kv = {"Rated entity": ["Acme"], "Country": ["DE"]}
        assert handle_industry_risk_nesting(kv) == kv
