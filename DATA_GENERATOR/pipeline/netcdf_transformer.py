"""Transform datasets into cleaned pandas DataFrames."""
from __future__ import annotations

import os
import sys

import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from DATA_GENERATOR.config import CANONICAL_COLUMNS


def dataset_to_dataframe(dataset) -> pd.DataFrame:
    """Convert an ARGO dataset wrapper into the canonical dataframe.

    Works with both the new Argovis DataWrapper and legacy xarray.Dataset.
    """
    if dataset is None:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    # Get the dataframe from the dataset wrapper
    df = dataset.to_dataframe()
    
    if df.empty:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)
    
    # Reset index if needed
    if df.index.name is not None or isinstance(df.index, pd.MultiIndex):
        df = df.reset_index()

    # Normalize column names to match the canonical schema (for legacy NetCDF)
    rename_map = {
        "platform_number": "float_id",
        "time": "timestamp",
        "pres": "pressure",
        "temp": "temperature",
        "psal": "salinity",
        "chla": "chlorophyll",
        "doxy": "dissolved_oxygen",
    }
    df = df.rename(columns=rename_map)

    # Convert timestamp if needed
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    
    # Drop rows lacking essential data
    df = df.dropna(subset=["timestamp", "float_id"])

    # Ensure all expected columns exist
    for column in CANONICAL_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA

    df = df[CANONICAL_COLUMNS]

    # Remove duplicates
    df = df.drop_duplicates(subset=["float_id", "timestamp", "pressure"], keep="last")
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Convert numeric columns
    numeric_columns = [col for col in CANONICAL_COLUMNS if col not in {"timestamp"}]
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors="coerce")

    return df
