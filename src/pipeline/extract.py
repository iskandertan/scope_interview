"""Excel extraction utilities."""

import logging
from pathlib import Path

import pandas as pd

from src.config import settings


logger = logging.getLogger(__name__)

SCOPE_MARKER = "[Scope Credit Metrics]"
MASTER_SHEET = "MASTER"


def extract_sheet_data(filepath: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Extract data from the MASTER sheet of the given Excel file.
    SCOPE_MARKER is used to split the sheet into 2 dataframes.
    The first dataframe contains all rows above the marker,
    and the second contains the marker row and all rows below it.
    """

    if not isinstance(filepath, Path):
        raise ValueError(f"Expected a Path object, got {type(filepath)}")

    df = pd.read_excel(filepath, sheet_name=MASTER_SHEET, dtype=object, header=None)

    # Drop columns and rows where every value is None/NaN
    df = df.dropna(axis=1, how="all").dropna(axis=0, how="all").reset_index(drop=True)

    mask = df.eq(SCOPE_MARKER).any(axis=1)  # type: ignore[arg-type]
    matches = df.index[mask].tolist()

    if not matches:
        raise ValueError(f"Marker '{SCOPE_MARKER}' not found in {filepath.name}")

    split_idx = int(matches[0])

    df_kv = df.iloc[:split_idx].reset_index(drop=True)
    df_ts = df.iloc[split_idx:].reset_index(drop=True)

    # If the last timeseries column is entirely "Locked", drop it.
    if not df_ts.empty and len(df_ts.columns) > 0:
        last_col = df_ts.iloc[:, -1]
        non_null = last_col.dropna()
        if not non_null.empty:
            all_locked = non_null.astype(str).str.strip().str.casefold().eq("locked").all()
            if all_locked:
                df_ts = df_ts.iloc[:, :-1]

    # Persist to data/parsed
    parsed_dir = settings.data_path / "parsed"
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

    return df_kv, df_ts
