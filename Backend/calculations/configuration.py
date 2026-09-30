"""Translate ExcelAnalyst's reviewable mappings into calculation settings."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class StageDefinition:
    """One ordered stage and the optional fields that can calculate its days."""

    label: str
    duration_column: Optional[str]
    start_column: Optional[str]
    end_column: Optional[str]


@dataclass(frozen=True)
class CalculationConfiguration:
    """All source-field dependencies selected by ExcelAnalyst."""

    identifier_column: Optional[str]
    group_column: Optional[str]
    onboarding_start_column: Optional[str]
    completion_column: Optional[str]
    stages: List[StageDefinition]


def _mapping_column(mapping: Any) -> Optional[str]:
    """Read a schema ColumnMapping without trusting an arbitrary response shape."""
    if not isinstance(mapping, dict):
        return None
    column = mapping.get("column")
    return column if isinstance(column, str) and column.strip() else None


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
            )
        )

    return CalculationConfiguration(
        identifier_column=_mapping_column(agent_response.get("identifier_mapping")),
        group_column=_mapping_column(agent_response.get("project_mapping")),
        onboarding_start_column=_mapping_column(agent_response.get("onboarding_start_mapping")),
        completion_column=_mapping_column(agent_response.get("onboarding_completion_mapping")),
        stages=stages,
    )
