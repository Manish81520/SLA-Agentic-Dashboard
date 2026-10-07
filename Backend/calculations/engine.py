"""Generic calculation engine for onboarding datasets."""

from collections import Counter
from datetime import date, timedelta
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from Backend.pipeline_config import FIXED_MAIN_STAGES, VALID_MAIN_STAGE_IDS
from .configuration import CalculationConfiguration, StageDefinition, configuration_from_agent
from .normalization import coerce_duration, json_value, normalize_dataframe, parse_iso_date, rounded, rounded_decimal


ANOMALY_Z_SCORE = 1.0
FOCUS_AREA_RATIO = 0.75


def _available_column(column: Optional[str], dataframe: pd.DataFrame) -> Optional[str]:
    return column if column in dataframe.columns else None


def _unresolved_columns(configuration: CalculationConfiguration, dataframe: pd.DataFrame) -> List[str]:
    """Columns the agent mapped that do not exist in the data (otherwise silently ignored)."""
    mapped: List[Optional[str]] = [
        configuration.identifier_column,
        configuration.partner_name_column,
        configuration.group_column,
        configuration.onboarding_start_column,
        configuration.completion_column,
    ]
    for stage in configuration.stages:
        mapped.extend([stage.duration_column, stage.start_column, stage.end_column])
    return sorted({column for column in mapped if column and column not in dataframe.columns})


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

    # Total onboarding duration: completed records only.
    #   1. Preferred: completion date - onboarding start date.
    #   2. Fallback (no start date): sum of stage values, but only when EVERY
    #      stage has a value, so partial sums never distort min/avg.
    # 0-day onboardings are valid and are kept.
    total_duration_values: List[Optional[float]] = []
    onboarding_start_column = _available_column(configuration.onboarding_start_column, dataframe)
    for index, row in dataframe.iterrows():
        total: Optional[float] = None
        start, _ = parse_iso_date(row[onboarding_start_column]) if onboarding_start_column else (None, "missing")
        completion, _ = parse_iso_date(row[completion_column]) if completion_column else (None, "missing")

        if completion is not None:  # only completed onboardings count
            if start is not None:
                total, _ = coerce_duration((completion - start).days)
            else:
                stage_vals = [stage_data[stage.label].loc[index] for stage in configuration.stages]
                if all(pd.notna(v) for v in stage_vals):
                    total, _ = coerce_duration(float(sum(stage_vals)))
        total_duration_values.append(total)

    total_duration = pd.Series(total_duration_values, index=dataframe.index, dtype="Float64")

    data_quality_issues = sum(
        sum(count for reason, count in issues.items() if reason != "missing")
        for issues in stage_quality.values()
    )
    filters_available = _categorical_filters(
        full_dataframe,
        [configuration.identifier_column, configuration.completion_column, *[stage.duration_column for stage in configuration.stages], *[stage.start_column for stage in configuration.stages], *[stage.end_column for stage in configuration.stages]],
    )

    pipeline = calculate_pipeline_from_data(dataframe, configuration, stage_data, stage_stats)
    stage_groups: List[Dict[str, Any]] = []
    for main_stage in pipeline["mainStages"]:
        stage_groups.append({
            "id": main_stage["id"],
            "name": main_stage["label"],
            "label": main_stage["label"],
            "order": main_stage["order"],
            "average": main_stage["averageDays"],
            "averageDays": main_stage["averageDays"],
            "trackedCount": main_stage["trackedCount"],
            "subStages": main_stage["subStages"],
        })
    if "unassigned" in pipeline:
        stage_groups.append({
            "id": "unassigned",
            "name": "Unassigned",
            "label": "Unassigned",
            "order": len(stage_groups) + 1,
            "average": None,
            "averageDays": None,
            "subStages": pipeline["unassigned"]["subStages"],
        })

    return {
        "schemaVersion": "1.0",
        "configuration": {
            "identifierColumn": identifier_column,
            "partnerNameColumn": _available_column(configuration.partner_name_column, dataframe),
            "groupColumn": group_column,
            "onboardingStartColumn": onboarding_start_column,
            "completionColumn": completion_column,
            "stages": [{"label": stage.label, "durationColumn": stage.duration_column, "startColumn": stage.start_column, "endColumn": stage.end_column, "mainStage": stage.main_stage} for stage in configuration.stages],
            # Agent-mapped columns that were not found in the data. Non-empty means
            # a mapping silently failed and should be reviewed.
            "unresolvedColumns": _unresolved_columns(configuration, full_dataframe),
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
        "stageGroups": stage_groups,
        "byGroup": by_group,
        "filters": filters_available,
        "activeFilters": filters,
        "records": records,
        "anomalyWatchlist": watchlist,
        "focusAreas": focus_areas,
        "dataQuality": stage_quality,
    }


def calculate_team_comparison(
    dataframe: pd.DataFrame,
    agent_response: Dict[str, Any],
    stage_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a stage-specific, team comparison with partner-level focus data.

    Team and partner names are read from the ExcelAnalyst mappings.  This
    deliberately keeps averages, comparison status, and anomaly thresholds out
    of the UI so the response stays correct for any uploaded dataset.
    """
    normalized_dataframe = normalize_dataframe(dataframe)
    configuration = configuration_from_agent(agent_response)
    if not configuration.stages:
        raise ValueError("ExcelAnalyst did not provide any stage mappings for comparison.")

    stages_by_label = {stage.label: stage for stage in configuration.stages}
    selected_stage = stages_by_label.get(stage_label) if stage_label else configuration.stages[0]
    if selected_stage is None:
        raise ValueError("The requested stage is not available in the active dataset.")

    selected_values, selected_quality, _ = _stage_values(normalized_dataframe, selected_stage)
    selected_stats = _stage_statistics(selected_values)
    overall_average = selected_stats["average"]
    anomaly_cutoff = selected_stats["anomalyCutoff"]

    group_column = _available_column(configuration.group_column, normalized_dataframe)
    partner_name_column = _available_column(configuration.partner_name_column, normalized_dataframe)
    completion_column = _available_column(configuration.completion_column, normalized_dataframe)
    stage_values = {
        stage.label: _stage_values(normalized_dataframe, stage)[0]
        for stage in configuration.stages
    }

    valid_indices = selected_values[selected_values.notna()].index
    team_values: Dict[str, List[float]] = {}
    partners: List[Dict[str, Any]] = []
    attention_count = 0
    approaching_average_count = 0
    anomaly_count = 0
    missing_partner_names = 0

    for row_number, row_index in enumerate(valid_indices, start=1):
        row = normalized_dataframe.loc[row_index]
        value = float(selected_values.loc[row_index])
        team_value = json_value(row[group_column]) if group_column else None
        team = str(team_value).strip() if team_value is not None and str(team_value).strip() else "Unspecified"
        partner_value = json_value(row[partner_name_column]) if partner_name_column else None
        partner_name = str(partner_value).strip() if partner_value is not None and str(partner_value).strip() else None

        current_stage = next(
            (
                stage.label
                for stage in reversed(configuration.stages)
                if pd.notna(stage_values[stage.label].loc[row_index])
            ),
            selected_stage.label,
        )
        difference = None if overall_average is None else value - overall_average
        is_complete = _is_complete(row, completion_column)
        is_active_stage = current_stage == selected_stage.label
        approaching_threshold = None if overall_average is None else FOCUS_AREA_RATIO * overall_average
        is_approaching = bool(
            not is_complete
            and is_active_stage
            and approaching_threshold is not None
            and value >= approaching_threshold
        )
        is_anomaly = bool(anomaly_cutoff is not None and value > anomaly_cutoff)

        team_values.setdefault(team, []).append(value)
        if not is_approaching:
            continue
        attention_count += 1
        if value < overall_average:
            approaching_average_count += 1
        if is_anomaly:
            anomaly_count += 1
        if partner_name is None:
            missing_partner_names += 1
            continue
        partners.append({
            "partnerName": partner_name,
            "team": team,
            "currentStage": current_stage,
            "stuckAtStage": current_stage,
            "onboardingStatus": "In progress",
            "actualOnboardingDays": rounded_decimal(value),
            "expectedAverageDays": rounded_decimal(overall_average),
            "differenceFromAverage": rounded_decimal(difference),
            "isAnomaly": is_anomaly,
            "attentionStatus": "potential_anomaly" if is_anomaly else "past_stage_average" if value >= overall_average else "approaching_stage_average",
        })

    teams = [
        {
            "team": team,
            "averageOnboardingDays": rounded_decimal(sum(values) / len(values)),
            "partnerCount": len(values),
        }
        for team, values in sorted(team_values.items(), key=lambda item: item[0].casefold())
        if values
    ]
    partners.sort(
        key=lambda partner: (
            not partner["isAnomaly"],
            -(partner["differenceFromAverage"] or 0),
            str(partner["partnerName"]).casefold(),
        )
    )

    return {
        "stages": [
            {"label": stage.label, "durationColumn": stage.duration_column}
            for stage in configuration.stages
        ],
        "selectedStage": selected_stage.label,
        "overallAverageDays": rounded_decimal(overall_average),
        "teams": teams,
        "focusArea": {
            "summary": {
                "partnersNeedingAttention": attention_count,
                "approachingStageAverage": approaching_average_count,
                "potentialAnomalies": anomaly_count,
                "partnersWithNames": len(partners),
                "missingPartnerNames": missing_partner_names,
            },
            "partners": partners,
        },
        "anomalyRule": {
            "method": "average_plus_one_standard_deviation",
            "thresholdDays": rounded_decimal(anomaly_cutoff),
        },
        "dataQuality": selected_quality,
    }


def _substage_summary(
    stage: StageDefinition,
    stage_data: Dict[str, pd.Series],
    stage_stats: Dict[str, Dict[str, Optional[float]]],
) -> tuple[Dict[str, Any], Optional[float]]:
    """Return the response row for one substage plus its UNROUNDED average."""
    raw_average = stage_stats.get(stage.label, {}).get("average")
    tracked = int(stage_data[stage.label].notna().sum()) if stage.label in stage_data else 0
    return (
        {
            "label": stage.label,
            "averageDays": rounded_decimal(raw_average, 1),
            "trackedCount": tracked,
        },
        raw_average,
    )


def calculate_pipeline_from_data(
    dataframe: pd.DataFrame,
    configuration: CalculationConfiguration,
    stage_data: Dict[str, pd.Series],
    stage_stats: Dict[str, Dict[str, Optional[float]]],
) -> Dict[str, Any]:
    """Roll up substages into the three fixed main pipeline stages.

    - Main-stage average days = SUM of its substages' UNROUNDED average days,
      rounded once at the end (summing already-rounded values would drift).
      Substages with no tracked data are skipped; if none have data, the
      average is null.
    - Substages keep the order the agent returned them in.
    - Substages with no valid main stage go into an extra "Unassigned" group,
      shown last and only if non-empty.
    - Always return the three main stages in fixed order, even if one has no
      substages (empty list, null average).
    - Pipeline averages are returned with one decimal place.
    """
    main_stages_result: List[Dict[str, Any]] = []

    for main_cfg in FIXED_MAIN_STAGES:
        matching_stages = [
            stage for stage in configuration.stages if stage.main_stage == main_cfg.id
        ]
        sub_stages: List[Dict[str, Any]] = []
        raw_averages: List[float] = []
        for stage in matching_stages:
            summary, raw_average = _substage_summary(stage, stage_data, stage_stats)
            sub_stages.append(summary)
            if raw_average is not None:
                raw_averages.append(raw_average)

        main_avg = rounded_decimal(sum(raw_averages), 1) if raw_averages else None

        main_tracked = 0
        if matching_stages and not dataframe.empty:
            tracked_frame = pd.concat(
                [stage_data[stage.label] for stage in matching_stages if stage.label in stage_data],
                axis=1,
            )
            main_tracked = int(tracked_frame.notna().any(axis=1).sum()) if not tracked_frame.empty else 0

        main_stages_result.append({
            "id": main_cfg.id,
            "label": main_cfg.label,
            "order": main_cfg.order,
            "averageDays": main_avg,
            "trackedCount": main_tracked,
            "subStages": sub_stages,
        })

    unassigned_sub_stages = [
        _substage_summary(stage, stage_data, stage_stats)[0]
        for stage in configuration.stages
        if stage.main_stage not in VALID_MAIN_STAGE_IDS
    ]

    response: Dict[str, Any] = {"mainStages": main_stages_result}
    if unassigned_sub_stages:
        response["unassigned"] = {"subStages": unassigned_sub_stages}
    return response


def calculate_pipeline(
    dataframe: pd.DataFrame,
    agent_response: Dict[str, Any],
    filters: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Calculate the 3-step onboarding pipeline roll-up."""
    full_dataframe = normalize_dataframe(dataframe)
    configuration: CalculationConfiguration = configuration_from_agent(agent_response)
    filters = filters or {}
    dataframe = _apply_filters(full_dataframe, filters)

    stage_data: Dict[str, pd.Series] = {}
    stage_stats: Dict[str, Dict[str, Optional[float]]] = {}
    for stage in configuration.stages:
        values, _, _ = _stage_values(dataframe, stage)
        stage_data[stage.label] = values
        stage_stats[stage.label] = _stage_statistics(values)

    return calculate_pipeline_from_data(dataframe, configuration, stage_data, stage_stats)
