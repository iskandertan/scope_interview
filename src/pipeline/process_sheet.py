"""Excel extraction utilities."""

import logging
from pathlib import Path

import pandas as pd

from src.config import settings
from src.pipeline.source_dtypes import SrcRawExcel


logger = logging.getLogger(__name__)

SPLIT_MARKER = "[Scope Credit Metrics]"
MASTER_SHEET = "MASTER"


def extract_sheet_data(filepath: Path) -> SrcRawExcel:
    """Split the MASTER sheet into key-value and timeseries sections at `SPLIT_MARKER`.
    Raises `ValueError` if `filepath` is not a `Path` or the marker is not found.
    """

    if not isinstance(filepath, Path):
        raise ValueError(f"Expected a Path object, got {type(filepath)}")

    try:
        df = pd.read_excel(filepath, sheet_name=MASTER_SHEET, dtype=object, header=None)
    except ValueError as exc:
        # TODO: handle this case
        if "Worksheet named" in str(exc) and f"'{MASTER_SHEET}'" in str(exc):
            logger.warning(
                f"Worksheet '{MASTER_SHEET}' not found in file '{filepath}', returning empty results."
            )
            return {}, {}
        raise

    split_idx = get_split_marker_row_index(df, marker=SPLIT_MARKER)
    df_kv, df_ts = split_dfs(df, split_idx)
    save_dfs(df_kv, df_ts, filepath)

    # Get kv_dict
    kv_dict: dict[str, list[str]] = {}
    for _, row in df_kv.iterrows():
        kv_dict[str(row.iloc[0])] = [str(v) for v in row.iloc[1:] if pd.notna(v)]
    kv_dict = handle_industry_risk_nesting(kv_dict)

    # Get ts_dict
    ts_dict = df_ts.set_index(df_ts.columns[0]).to_dict("index")

    return SrcRawExcel(key_values=kv_dict, timeseries=ts_dict)


def handle_industry_risk_nesting(kv_dict: dict) -> dict:
    """
    Group properties under "Industry Risk" into nested dicts.
    Everything between "Industry Risk" (excluding) and "Segmentation Criteria" (excluding) is
    included in the Industry Risk group.
    """

    def norm(k: str) -> str:
        return k.strip().casefold()

    keys = list(kv_dict.keys())
    normed = [norm(k) for k in keys]

    if "industry risk" not in normed:
        return kv_dict

    start = normed.index("industry risk")
    end = (
        normed.index("segmentation criteria", start)
        if "segmentation criteria" in normed[start:]
        else len(keys)
    )

    industry_key = keys[start]
    prop_keys = keys[start + 1 : end]
    industry_names = kv_dict[industry_key]

    kv_dict[industry_key] = [
        {name: {pk: kv_dict[pk][i] for pk in prop_keys if i < len(kv_dict[pk])}}
        for i, name in enumerate(industry_names)
    ]
    for pk in prop_keys:
        del kv_dict[pk]

    return kv_dict


def split_dfs(df, split_idx):

    df_kv = df.iloc[:split_idx].reset_index(drop=True)
    df_kv = (
        df_kv.dropna(axis=1, how="all").dropna(axis=0, how="all").reset_index(drop=True)
    )

    df_ts = df.iloc[split_idx:].reset_index(drop=True)
    df_ts.columns = df_ts.iloc[0]
    df_ts = df_ts.iloc[1:].reset_index(drop=True)

    # If the last timeseries column is entirely "Locked", drop it.
    if not df_ts.empty and len(df_ts.columns) > 0:
        last_col = df_ts.iloc[:, -1]
        non_null = last_col.dropna()
        if not non_null.empty:
            all_locked = (
                non_null.astype(str).str.strip().str.casefold().eq("locked").all()
            )
            if all_locked:
                df_ts = df_ts.iloc[:, :-1]
    df_ts = (
        df_ts.dropna(axis=1, how="all").dropna(axis=0, how="all").reset_index(drop=True)
    )

    return df_kv, df_ts


def get_split_marker_row_index(df: pd.DataFrame, marker=SPLIT_MARKER) -> int:
    """Return the index of the first row containing SPLIT_MARKER in any column."""
    mask = df.eq(marker).any(axis=1)  # type: ignore[arg-type]
    matches = df.index[mask].tolist()
    if not matches:
        raise ValueError(f"Marker '{marker}' not found in DataFrame")
    return int(matches[0])


def save_dfs(df_kv: pd.DataFrame, df_ts: pd.DataFrame, filepath: Path) -> None:
    """Save the given DataFrames to Excel files in the parsed directory.
    Used for debugging to see what the split DFs look like"""
    parsed_dir = settings.data_path / "debug"
    parsed_dir.mkdir(parents=True, exist_ok=True)

    stem = filepath.stem
    kv_path = parsed_dir / f"{stem}_kv.xlsx"
    ts_path = parsed_dir / f"{stem}_ts.xlsx"

    if not kv_path.exists():
        df_kv.to_excel(kv_path, index=False, header=False)
        logger.info(f"Saved {kv_path}")

    if not ts_path.exists():
        df_ts.to_excel(ts_path, index=False, header=False)
        logger.info(f"Saved {ts_path}")
