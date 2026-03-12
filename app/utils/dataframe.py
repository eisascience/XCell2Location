"""DataFrame utilities for pandas."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)


def load_dataframe(
    path: Path,
    index_col: Optional[Union[int, str]] = 0,
    **kwargs: Any,
) -> pd.DataFrame:
    """Load a CSV, TSV, or Parquet file into a DataFrame.

    Args:
        path: Path to the file.
        index_col: Column to use as the row index.
        **kwargs: Passed to the underlying pandas reader.

    Returns:
        Loaded DataFrame.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".csv",):
        return pd.read_csv(path, index_col=index_col, **kwargs)
    elif suffix in (".tsv", ".txt"):
        return pd.read_csv(path, sep="\t", index_col=index_col, **kwargs)
    elif suffix in (".parquet",):
        return pd.read_parquet(path, **kwargs)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def save_dataframe(
    df: pd.DataFrame,
    path: Path,
    fmt: str = "csv",
    **kwargs: Any,
) -> Path:
    """Save a DataFrame to disk.

    Args:
        df: DataFrame to save.
        path: Destination path.
        fmt: Output format ('csv', 'parquet', 'tsv').
        **kwargs: Passed to the underlying writer.

    Returns:
        Resolved output path.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "csv":
        df.to_csv(path, **kwargs)
    elif fmt == "parquet":
        df.to_parquet(path, engine="pyarrow", **kwargs)
    elif fmt == "tsv":
        df.to_csv(path, sep="\t", **kwargs)
    else:
        raise ValueError(f"Unsupported format: {fmt}")
    return path


def pivot_cell_type_abundance(
    df: pd.DataFrame,
    spot_col: str = "spot",
    cell_type_col: str = "cell_type",
    value_col: str = "abundance",
) -> pd.DataFrame:
    """Pivot a long-format abundance table to wide format.

    Returns:
        DataFrame with spots as rows and cell types as columns.
    """
    return df.pivot_table(index=spot_col, columns=cell_type_col, values=value_col, aggfunc="sum")


def normalise_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Row-normalise a DataFrame so each row sums to 1."""
    row_sums = df.sum(axis=1).replace(0, 1)
    return df.div(row_sums, axis=0)


def summarise(df: pd.DataFrame) -> Dict[str, Any]:
    """Return a basic summary of a DataFrame."""
    return {
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": df.dtypes.to_dict(),
        "null_counts": df.isnull().sum().to_dict(),
        "numeric_stats": df.describe().to_dict() if df.select_dtypes("number").shape[1] > 0 else {},
    }
