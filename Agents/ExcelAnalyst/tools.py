"""
Tools for inspecting spreadsheet files (Excel .xlsx/.xls and CSV .csv)
without hardcoding any column names or onboarding stages.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import os
import re
import pandas as pd


try:
    from .data_cleaner import clean_dataframe
except ImportError:
    try:
        from Agents.ExcelAnalyst.data_cleaner import clean_dataframe
    except ImportError:
        from .data_cleaner import clean_dataframe


def _find_default_data_file() -> Optional[Path]:
    """Find the first available spreadsheet (csv, xlsx, xls) in the Data directory."""
    possible_dirs = [
        Path("Data"),
        Path(__file__).resolve().parent.parent.parent / "Data",
        Path.cwd() / "Data",
    ]
    for data_dir in possible_dirs:
        if data_dir.exists() and data_dir.is_dir():
            for ext in ("*.csv", "*.xlsx", "*.xls"):
                files = list(data_dir.glob(ext))
                if files:
                    return files[0]
    return None


def _is_date_like(val_str: str) -> bool:
    """Heuristic check if a sample string looks like a date/time."""
    val = val_str.strip()
    if not val or len(val) < 6 or len(val) > 30:
        return False
    date_patterns = [
        r"^\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}$",
        r"^\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}\s+\d{1,2}:\d{2}",
    ]
    for pattern in date_patterns:
        if re.match(pattern, val):
            return True
    return False


def inspect_spreadsheet(file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Inspects an Excel (.xlsx, .xls) or CSV (.csv) file, cleans it, and extracts
    structural metadata.

    This tool reads the file using Pandas/openpyxl, runs it through the generic
    data-cleaning step, then gathers column details, sample values, data types,
    and null counts so the agent can understand the dataset dynamically.
    No column names or stage names are hardcoded.

    Args:
        file_path: Optional path to the file. If not provided, it automatically
                   searches for the first spreadsheet in the 'Data' folder.

    Returns:
        A dictionary containing dataset statistics, columns, data types, sample
        values, potential date candidates, and a cleaning_report describing what
        was fixed before analysis.
    """
    if file_path is None or not str(file_path).strip():
        detected_path = _find_default_data_file()
        if not detected_path:
            return {
                "error": "No data file found in the Data folder. Please specify file_path."
            }
        target_path = detected_path
    else:
        target_path = Path(file_path)

    if not target_path.exists():
        return {"error": f"File not found at path: {target_path}"}

    file_suffix = target_path.suffix.lower()
    sheet_names = []

    try:
        if file_suffix == ".csv":
            df = pd.read_csv(target_path, encoding="utf-8-sig")
            file_type = "csv"
        elif file_suffix in [".xlsx", ".xls"]:
            excel_file = pd.ExcelFile(target_path)
            sheet_names = excel_file.sheet_names
            df = pd.read_excel(target_path, sheet_name=0)
            file_type = "excel"
        else:
            return {
                "error": f"Unsupported file type: '{file_suffix}'. Please provide .xlsx, .xls, or .csv"
            }
    except Exception as exc:
        return {"error": f"Failed to read file '{target_path.name}': {str(exc)}"}

    # Clean the raw data before analyzing it
    df, cleaning_report = clean_dataframe(df)

    total_rows, total_cols = df.shape
    columns_info: List[Dict[str, Any]] = []

    for col in df.columns:
        col_str = str(col)
        cleaned_name = col_str.strip()
        series = df[col]

        non_null_series = series.dropna()
        null_count = int(series.isna().sum())
        null_pct = round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0.0

        unique_samples = [str(x).strip() for x in non_null_series.unique()[:5]]

        name_lower = cleaned_name.lower()
        has_date_keyword = any(kw in name_lower for kw in ["date", "time", "day", "initiated", "completed"])
        samples_look_like_dates = any(_is_date_like(s) for s in unique_samples)
        is_potential_date = has_date_keyword or samples_look_like_dates

        has_whitespace_issue = col_str != cleaned_name

        columns_info.append({
            "original_name": col_str,
            "cleaned_name": cleaned_name,
            "has_whitespace_padding": has_whitespace_issue,
            "dtype": str(series.dtype),
            "sample_values": unique_samples,
            "null_count": null_count,
            "null_percentage": null_pct,
            "unique_count": int(non_null_series.nunique()),
            "is_potential_date": is_potential_date,
        })

    preview_rows = df.head(2).fillna("").to_dict(orient="records")
    clean_preview = [
        {str(k): str(v) for k, v in row.items()}
        for row in preview_rows
    ]

    return {
        "file_name": target_path.name,
        "file_path": str(target_path.resolve()),
        "file_type": file_type,
        "sheet_names": sheet_names,
        "total_rows": total_rows,
        "total_columns": total_cols,
        "column_names": [str(c) for c in df.columns],
        "columns_analysis": columns_info,
        "preview_rows": clean_preview,
        "cleaning_report": cleaning_report,
    }