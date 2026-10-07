"""Alcance reproducible del análisis sobre los registros descargados."""
from datetime import date

import pandas as pd


def apply_analysis_scope(
    df: pd.DataFrame,
    date_column: str = "",
    period: tuple[date | None, date | None] | None = None,
    sample_rows: int | None = None,
) -> pd.DataFrame:
    result = df
    if date_column and date_column in df.columns and period:
        dates = pd.to_datetime(result[date_column], errors="coerce")
        start, end = period
        if start is not None:
            result = result.loc[dates.dt.date >= start]
            dates = dates.loc[result.index]
        if end is not None:
            result = result.loc[dates.dt.date <= end]
    if sample_rows is not None and len(result) > sample_rows:
        result = result.sample(n=max(1, sample_rows), random_state=42).sort_index()
    return result.copy()
