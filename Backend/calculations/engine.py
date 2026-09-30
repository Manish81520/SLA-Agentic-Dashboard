"""Generic calculation engine for onboarding datasets."""

from collections import Counter
from datetime import date, timedelta
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from .configuration import CalculationConfiguration, StageDefinition, configuration_from_agent
from .normalization import coerce_duration, json_value, normalize_dataframe, parse_iso_date, rounded


ANOMALY_Z_SCORE = 1.0
FOCUS_AREA_RATIO = 0.75


def _available_column(column: Optional[str], dataframe: pd.DataFrame) -> Optional[str]:
    return column if column in dataframe.columns else None


def _stage_values(
    dataframe: pd.DataFrame,
    stage: StageDefinition,
) -> tuple[pd.Series, Dict[str, int], List[str]]:
    """Use a supplied duration, or derive it from mapped ISO dates per record."""
    values: List[Optional[float]] = []
    quality = Counter()
    sources: List[str] = []
    duration_column = _available_column(stage.duration_column, dataframe)
    start_column = _available_column(stage.start_column, dataframe)
    end_column = _available_column(stage.end_column, dataframe)

    for _, row in dataframe.iterrows():
        value: Optional[float] = None
        source = "missing"
        if duration_column:
            value, reason = coerce_duration(row[duration_column])
            if value is not None:
                source = "provided_duration"
            elif reason != "missing":
                quality[reason] += 1

        if value is None and start_column and end_column:
            start, start_reason = parse_iso_date(row[start_column])
            end, end_reason = parse_iso_date(row[end_column])
            if start is not None and end is not None:
                value, duration_reason = coerce_duration((end - start).days)
                if value is not None:
                    source = "derived_from_dates"
                else:
                    quality[duration_reason or "invalid_duration"] += 1
            elif start_reason not in (None, "missing") or end_reason not in (None, "missing"):
                quality["invalid_date"] += 1

        if value is None:
            quality["missing"] += 1
        values.append(value)
        sources.append(source)
    return pd.Series(values, index=dataframe.index, dtype="Float64"), dict(quality), sources


def _stage_statistics(values: pd.Series) -> Dict[str, Optional[float]]:
    valid = values.dropna()
    if valid.empty:
        return {"average": None, "std": None, "anomalyCutoff": None, "minimum": None, "maximum": None}
    average = float(valid.mean())
    standard_deviation = float(valid.std()) if len(valid) > 1 else 0.0
    return {
        "average": average,
        "std": standard_deviation,
        "anomalyCutoff": average + ANOMALY_Z_SCORE * standard_deviation,
        "minimum": float(valid.min()),
        "maximum": float(valid.max()),
    }


def _is_complete(row: pd.Series, completion_column: Optional[str]) -> bool:
    if not completion_column:
        return False
    completed_at, _ = parse_iso_date(row[completion_column])
    return completed_at is not None


def _categorical_filters(dataframe: pd.DataFrame, excluded_columns: Iterable[Optional[str]]) -> Dict[str, List[str]]:
    excluded = {column for column in excluded_columns if column}
    filters: Dict[str, List[str]] = {}
    for column in dataframe.columns:
        if column in excluded or pd.api.types.is_numeric_dtype(dataframe[column]):
            continue
        values = [str(value).strip() for value in dataframe[column].dropna().unique() if str(value).strip()]
        if 1 < len(values) <= 50:
            filters[column] = sorted(values)
    return filters


def _apply_filters(dataframe: pd.DataFrame, filters: Dict[str, str]) -> pd.DataFrame:
    filtered = dataframe
    for column, value in filters.items():
        if column in filtered.columns and value:
            filtered = filtered[filtered[column].astype(str).str.strip() == value]
    return filtered


def calculate_dataset(
    dataframe: pd.DataFrame,
    agent_response: Dict[str, Any],
    filters: Optional[Dict[str, str]] = None,
    analysis_date: Optional[date] = None,
) -> Dict[str, Any]:
    """Calculate all generic dashboard metrics from data and agent mappings.

    The agent supplies semantic field mappings; deterministic code owns every
    calculation thereafter. No team, stage, person, project, or row position is
    embedded in the engine.
    """
    full_dataframe = normalize_dataframe(dataframe)
    configuration: CalculationConfiguration = configuration_from_agent(agent_response)
    if not configuration.stages:
        raise ValueError("ExcelAnalyst did not provide any stage mappings for calculation.")
    filters = filters or {}
    dataframe = _apply_filters(full_dataframe, filters)
    completion_column = _available_column(configuration.completion_column, dataframe)
    group_column = _available_column(configuration.group_column, dataframe)
    identifier_column = _available_column(configuration.identifier_column, dataframe)

    stage_data: Dict[str, pd.Series] = {}
    stage_sources: Dict[str, List[str]] = {}
    stage_quality: Dict[str, Dict[str, int]] = {}
    stage_stats: Dict[str, Dict[str, Optional[float]]] = {}
    for stage in configuration.stages:
        values, quality, sources = _stage_values(dataframe, stage)
        stage_data[stage.label] = values
        stage_sources[stage.label] = sources
        stage_quality[stage.label] = quality
        stage_stats[stage.label] = _stage_statistics(values)

    stage_summaries: List[Dict[str, Any]] = []
    total_anomalies = 0
    for stage in configuration.stages:
        values = stage_data[stage.label]
        stats = stage_stats[stage.label]
        cutoff = stats["anomalyCutoff"]
        anomaly_count = int((values > cutoff).sum()) if cutoff is not None else 0
        total_anomalies += anomaly_count
        stage_summaries.append({
            "label": stage.label,
            "durationColumn": stage.duration_column,
            "startColumn": stage.start_column,
            "endColumn": stage.end_column,
            "average": rounded(stats["average"]),
            "std": rounded(stats["std"]),
            "anomalyCutoff": rounded(cutoff),
            "minimum": rounded(stats["minimum"]),
            "maximum": rounded(stats["maximum"]),
            "anomalyCount": anomaly_count,
            "trackedCount": int(values.notna().sum()),
            "dataQuality": stage_quality[stage.label],
        })

    records: List[Dict[str, Any]] = []
    watchlist: List[Dict[str, Any]] = []
    focus_areas: List[Dict[str, Any]] = []
    today = analysis_date or date.today()
    for position, (row_index, row) in enumerate(dataframe.iterrows(), start=1):
        raw_fields = {column: json_value(value) for column, value in row.items()}
        record_id = json_value(row[identifier_column]) if identifier_column else None
        record_id = record_id if record_id is not None else str(row_index)
        group = json_value(row[group_column]) if group_column else None
        group = group if group is not None else "Unspecified"
        complete = _is_complete(row, completion_column)
        stage_rows: List[Dict[str, Any]] = []
        anomalies: Dict[str, Optional[bool]] = {}
        stage_values: Dict[str, Optional[int]] = {}

        for stage in configuration.stages:
            label = stage.label
            value = stage_data[label].loc[row_index]
            value = None if pd.isna(value) else float(value)
            stats = stage_stats[label]
            cutoff = stats["anomalyCutoff"]
            average = stats["average"]
            is_anomaly = None if value is None else bool(cutoff is not None and value > cutoff)
            deviation = None if value is None or average is None else value - average
            stage_rows.append({
                "label": label,
                "value": rounded(value),
                "average": rounded(average),
                "deviation": rounded(deviation),
                "isAnomaly": is_anomaly,
                "source": stage_sources[label][position - 1],
            })
            anomalies[label] = is_anomaly
            stage_values[label] = rounded(value)
            if is_anomaly:
                standard_deviation = stats["std"]
                watchlist.append({
                    "recordId": record_id,
                    "group": group,
                    "stage": label,
                    "value": rounded(value),
                    "average": rounded(average),
                    "deviation": rounded(deviation),
                    "zScore": rounded(deviation / standard_deviation) if standard_deviation else None,
                    "_sort": deviation or 0,
                })
            if not complete and value is not None and average and cutoff is not None:
                threshold = FOCUS_AREA_RATIO * average
                if threshold <= value <= cutoff:
                    focus_areas.append({
                        "recordId": record_id,
                        "group": group,
                        "stage": label,
                        "value": rounded(value),
                        "average": rounded(average),
                        "percentOfAverage": rounded(value / average * 100),
                        "_sort": value / average,
                    })

        current_stage = next((stage for stage in reversed(stage_rows) if stage["value"] is not None), None)
        forecast = None
        if not complete and current_stage and current_stage["average"] is not None:
            remaining = current_stage["average"] - current_stage["value"]
            forecast = {
                "currentStage": current_stage["label"],
                "daysRemaining": rounded(max(remaining, 0)),
                "overdueDays": rounded(abs(remaining)) if remaining < 0 else 0,
                "predictedCompletionDate": (today + timedelta(days=max(round(remaining), 0))).isoformat(),
                "status": "overdue" if remaining < 0 else "at_risk" if current_stage["value"] >= FOCUS_AREA_RATIO * current_stage["average"] else "on_track",
            }
        record = {
            "recordId": record_id,
            "group": group,
            "isComplete": complete,
            "fields": raw_fields,
            "stages": stage_rows,
            "forecast": forecast,
            "_anomalies": anomalies,
            "_stageValues": stage_values,
        }
        for field_name, field_value in raw_fields.items():
            record.setdefault(field_name, field_value)
        records.append(record)

    groups = ["All"] if not group_column else sorted(str(value) for value in dataframe[group_column].dropna().unique())
    by_group: List[Dict[str, Any]] = []
    for group in groups:
        subset = dataframe if not group_column else dataframe[dataframe[group_column].astype(str) == group]
        entry: Dict[str, Any] = {"group": group, "recordCount": int(len(subset)), "stageMetrics": {}}
        for stage in configuration.stages:
            average = stage_data[stage.label].loc[subset.index].mean()
            average = None if pd.isna(average) else float(average)
            global_average = stage_stats[stage.label]["average"]
            entry[stage.label] = rounded(average)
            entry[f"{stage.label}__vsAvg"] = rounded(average - global_average) if average is not None and global_average is not None else None
            entry["stageMetrics"][stage.label] = {
                "average": rounded(average),
                "vsGlobalAverage": entry[f"{stage.label}__vsAvg"],
            }
        by_group.append(entry)

    watchlist.sort(key=lambda item: item.pop("_sort"), reverse=True)
    focus_areas.sort(key=lambda item: item.pop("_sort"), reverse=True)
    total_duration_values: List[Optional[float]] = []
    onboarding_start_column = _available_column(configuration.onboarding_start_column, dataframe)
    for index, row in dataframe.iterrows():
        start, _ = parse_iso_date(row[onboarding_start_column]) if onboarding_start_column else (None, "missing")
        completion, _ = parse_iso_date(row[completion_column]) if completion_column else (None, "missing")
        if start is not None and completion is not None:
            value, _ = coerce_duration((completion - start).days)
            total_duration_values.append(value)
            continue
        stage_total = sum(stage_data[stage.label].loc[index] for stage in configuration.stages if pd.notna(stage_data[stage.label].loc[index]))
        total_duration_values.append(float(stage_total) if stage_total else None)
    total_duration = pd.Series(total_duration_values, dtype="Float64")
    total_duration = total_duration.where(total_duration > 0, pd.NA)
    data_quality_issues = sum(
        sum(count for reason, count in issues.items() if reason != "missing")
        for issues in stage_quality.values()
    )
    filters_available = _categorical_filters(
        full_dataframe,
        [configuration.identifier_column, configuration.completion_column, *[stage.duration_column for stage in configuration.stages], *[stage.start_column for stage in configuration.stages], *[stage.end_column for stage in configuration.stages]],
    )

    return {
        "schemaVersion": "1.0",
        "configuration": {
            "identifierColumn": identifier_column,
            "groupColumn": group_column,
            "onboardingStartColumn": onboarding_start_column,
            "completionColumn": completion_column,
            "stages": [{"label": stage.label, "durationColumn": stage.duration_column, "startColumn": stage.start_column, "endColumn": stage.end_column} for stage in configuration.stages],
        },
        "kpis": {
            "totalRecords": int(len(dataframe)),
            "totalAnomalies": total_anomalies,
            "groupCount": int(len(groups)) if group_column else 0,
            "averageTotalDuration": rounded(total_duration.mean()),
            "minimumTotalDuration": rounded(total_duration.min()),
            "maximumTotalDuration": rounded(total_duration.max()),
            "dataQualityIssues": data_quality_issues,
        },
        "stages": stage_summaries,
        "stageGroups": [{"name": stage["label"], "average": stage["average"], "anomalyCount": stage["anomalyCount"], "subStages": [stage]} for stage in stage_summaries],
        "byGroup": by_group,
        "filters": filters_available,
        "activeFilters": filters,
        "records": records,
        "anomalyWatchlist": watchlist,
        "focusAreas": focus_areas,
        "dataQuality": stage_quality,
    }
