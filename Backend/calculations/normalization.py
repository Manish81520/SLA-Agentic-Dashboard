"""Raw-data normalization and safe coercion utilities for calculations."""

import math
import re
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd


MIN_PLAUSIBLE_DAYS = 0
MAX_PLAUSIBLE_DAYS = 365
NULL_LIKE_VALUES = {"", "na", "n/a", "null", "none", "nan"}


def normalize_header(value: Any) -> str:
    """Normalize only whitespace; preserve the source header's actual words."""
    return re.sub(r"\s+", " ", str(value).strip())


def normalize_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Copy raw input, normalize headers, and reject duplicate cleaned headers."""
    normalized = dataframe.copy()
    normalized.columns = [normalize_header(column) for column in normalized.columns]
    duplicates = normalized.columns[normalized.columns.duplicated()].tolist()
    if duplicates:
        raise ValueError(f"Duplicate column names after whitespace normalization: {duplicates}")
    return normalized


def coerce_duration(value: Any) -> tuple[Optional[float], Optional[str]]:
    """Return a plausible day count or a reason it cannot be used."""
    if value is None or (isinstance(value, str) and value.strip().lower() in NULL_LIKE_VALUES):
        return None, "missing"
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric) or not math.isfinite(float(numeric)):
        return None, "invalid_numeric"
    numeric = float(numeric)
    if numeric < MIN_PLAUSIBLE_DAYS or numeric > MAX_PLAUSIBLE_DAYS:
        return None, "outside_plausible_range"
    return numeric, None


def parse_iso_date(value: Any) -> tuple[Optional[datetime], Optional[str]]:
    """Parse only the project's accepted year-first CSV date formats."""
    if value is None or (isinstance(value, str) and value.strip().lower() in NULL_LIKE_VALUES):
        return None, "missing"
    if isinstance(value, datetime):
        return value, None
    text = str(value).strip()
    for date_format in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, date_format), None
        except ValueError:
            continue
    return None, "invalid_date"


def json_value(value: Any) -> Any:
    """Convert pandas/numpy scalars and nulls into JSON-safe Python values."""
    if value is None or pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def rounded(value: Optional[float]) -> Optional[int]:
    """Apply the reference dashboard's whole-number response policy."""
    return None if value is None or pd.isna(value) else int(round(float(value)))
