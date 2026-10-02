"""Translate ExcelAnalyst's reviewable mappings into calculation settings."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from Backend.pipeline_config import VALID_MAIN_STAGE_IDS
from .normalization import normalize_header


@dataclass(frozen=True)
class StageDefinition:
    """One ordered stage and the optional fields that can calculate its days."""

    label: str
    duration_column: Optional[str]
    start_column: Optional[str]
    end_column: Optional[str]
    main_stage: Optional[str] = None


@dataclass(frozen=True)
class CalculationConfiguration:
    """All source-field dependencies selected by ExcelAnalyst."""

    identifier_column: Optional[str]
    group_column: Optional[str]
    onboarding_start_column: Optional[str]
    completion_column: Optional[str]
    stages: List[StageDefinition]


def _mapping_column(mapping: Any) -> Optional[str]:
    """Read a schema ColumnMapping without trusting an arbitrary response shape.

    The header is passed through the same whitespace normalization the engine
    applies to the dataframe, so a header such as "Onboarding  Documents ..."
    (double space) still resolves to its column instead of being silently dropped.
    """
    if not isinstance(mapping, dict):
        return None
    column = mapping.get("column")
    if isinstance(column, str) and column.strip():
        return normalize_header(column)
    return None


def _main_stage_id(mapping: Any) -> Optional[str]:
    """Extract and validate the fixed main stage ID from main_stage_mapping."""
    if isinstance(mapping, str):
        val = mapping.strip()
        return val if val in VALID_MAIN_STAGE_IDS else None
    if not isinstance(mapping, dict):
        return None
    val = (
        mapping.get("stage_id")
        or mapping.get("column")
        or mapping.get("id")
        or mapping.get("main_stage")
    )
    if isinstance(val, str) and val.strip() in VALID_MAIN_STAGE_IDS:
        return val.strip()
    return None


def configuration_from_agent(agent_response: Dict[str, Any]) -> CalculationConfiguration:
    """Build generic settings from the mappings returned by ExcelAnalyst.

    No source header is named here. Stages remain in the order provided by the
    agent, which is the only safe generic ordering signal available.
    """
    stages: List[StageDefinition] = []
    labels_in_use: set[str] = set()
    for index, raw_stage in enumerate(agent_response.get("stages", []), start=1):
        if not isinstance(raw_stage, dict):
            continue
        base_label = str(raw_stage.get("stage_name") or f"Stage {index}").strip()
        label = base_label or f"Stage {index}"
        suffix = 2
        while label in labels_in_use:
            label = f"{base_label} ({suffix})"
            suffix += 1
        labels_in_use.add(label)
        stages.append(
            StageDefinition(
                label=label,
                duration_column=_mapping_column(raw_stage.get("duration_mapping")),
                start_column=_mapping_column(raw_stage.get("start_mapping")),
                end_column=_mapping_column(raw_stage.get("end_mapping")),
                main_stage=_main_stage_id(raw_stage.get("main_stage_mapping")),
            )
        )

    return CalculationConfiguration(
        identifier_column=_mapping_column(agent_response.get("identifier_mapping")),
        group_column=_mapping_column(agent_response.get("project_mapping")),
        onboarding_start_column=_mapping_column(agent_response.get("onboarding_start_mapping")),
        completion_column=_mapping_column(agent_response.get("onboarding_completion_mapping")),
        stages=stages,
    )