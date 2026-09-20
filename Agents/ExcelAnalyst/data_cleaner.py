"""
Deterministic, generic data cleaning for onboarding spreadsheets.

This runs BEFORE the ExcelAnalyst agent ever sees the data — cleaning is a
mechanical, rule-based step and should never be left to the LLM, per the
project's separation of concerns (Agent = understand, Backend = calculate).

Like tools.py, this module knows nothing about specific column names or
onboarding stages — it stays generic across different client spreadsheets.
"""

import re
from datetime import datetime
from typing import Any, Dict, Tuple
import pandas as pd

NULL_LIKE_TOKENS = {"", "na", "n/a", "null", "none", "-", "nil", "nan"}
DATE_NAME_KEYWORDS = ("date", "time", "day")
NUMERIC_COLUMN_THRESHOLD = 0.8
ISO_DATE_PATTERN = re.compile(r"^\d{4}([-/])\d{2}\1\d{2}$")


def is_supported_iso_date(value: Any) -> bool:
    """Return whether a value is a calendar-valid supported CSV date.

    Dates are accepted only when the year appears first, as ``YYYY-MM-DD`` or
    ``YYYY/MM/DD``. Parsing is deliberately format-specific so this helper can
    never infer whether a value such as ``06/06/2006`` is day-first or
    month-first.
    """
    if not isinstance(value, str):
        return False

    match = ISO_DATE_PATTERN.fullmatch(value.strip())
    if not match:
        return False

    date_format = "%Y-%m-%d" if match.group(1) == "-" else "%Y/%m/%d"
    try:
        datetime.strptime(value.strip(), date_format)
    except ValueError:
        return False
    return True


def _is_mostly_numeric(series: pd.Series) -> bool:
    """Return whether a populated column represents numeric values.

    Header text is not sufficient evidence for a date: a duration field may
    legitimately be called something like ``SLA Start Date``. Treat a column
    as numeric when at least 80% of its populated values coerce to numbers,
    protecting duration and SLA values from date parsing.
    """
    non_null = series.dropna()
    if non_null.empty:
        return False
    if pd.api.types.is_numeric_dtype(series):
        return True
    numeric_count = pd.to_numeric(non_null, errors="coerce").notna().sum()
    return (numeric_count / len(non_null)) >= NUMERIC_COLUMN_THRESHOLD


def clean_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Applies generic, safe cleaning steps to a raw onboarding dataframe and
    returns (cleaned_df, report). The report documents every change made,
    so nothing is altered silently - useful for debugging and for the
    "human confirmation" step your project plan calls for later.

    Steps:
      1. Strip whitespace from column headers.
      2. Normalize null-like text ("NA", "N/A", "-", "null", "", etc.) to real NaN.
      3. Strip whitespace from string cell values.
      4. Drop fully-empty rows.
      5. Drop exact duplicate rows (keeps first occurrence).
      6. Canonicalize already-valid ISO-style date columns to YYYY-MM-DD.
         This function never infers a day/month ordering.
    """
    report: Dict[str, Any] = {
        "original_shape": list(df.shape),
        "renamed_columns": [],
        "null_like_values_normalized": 0,
        "empty_rows_dropped": 0,
        "duplicate_rows_dropped": 0,
        "columns_parsed_as_dates": [],
        "columns_skipped_date_parse": [],
    }

    df = df.copy()

    # 1. Clean column headers
    rename_map = {}
    for col in df.columns:
        cleaned = str(col).strip()
        if cleaned != col:
            rename_map[col] = cleaned
    if rename_map:
        df = df.rename(columns=rename_map)
        report["renamed_columns"] = [{"from": k, "to": v} for k, v in rename_map.items()]

    # 2 & 3. Normalize null-like tokens and strip whitespace on string cells
    def _normalize_cell(value: Any) -> Any:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.lower() in NULL_LIKE_TOKENS:
                return pd.NA
            return stripped
        return value

    before_na = int(df.isna().sum().sum())
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].map(_normalize_cell)
    after_na = int(df.isna().sum().sum())
    report["null_like_values_normalized"] = after_na - before_na

    # 4. Drop fully-empty rows
    fully_empty_mask = df.isna().all(axis=1)
    report["empty_rows_dropped"] = int(fully_empty_mask.sum())
    df = df[~fully_empty_mask]

    # 5. Drop exact duplicate rows (keep first)
    duplicate_mask = df.duplicated(keep="first")
    report["duplicate_rows_dropped"] = int(duplicate_mask.sum())
    df = df[~duplicate_mask]

    # 6. Canonicalize only explicit ISO-style dates. CSV validation happens
    # before this function is called; this guard also keeps direct callers from
    # accidentally applying an inferred date convention.
    for col in df.columns:
        name_lower = col.lower()
        looks_date_named = any(kw in name_lower for kw in DATE_NAME_KEYWORDS)
        if not looks_date_named or _is_mostly_numeric(df[col]):
            continue

        if df[col].notna().sum() == 0:
            continue

        non_null_values = df.loc[df[col].notna(), col]
        if non_null_values.map(is_supported_iso_date).all():
            parsed = pd.to_datetime(non_null_values, format="mixed", errors="raise")
            df.loc[non_null_values.index, col] = parsed.dt.strftime("%Y-%m-%d")
            report["columns_parsed_as_dates"].append(col)
        else:
            report["columns_skipped_date_parse"].append(col)

    df = df.reset_index(drop=True)
    report["final_shape"] = list(df.shape)
    return df, report
