"""Fixed main onboarding pipeline stage definitions."""

from dataclasses import dataclass
from typing import List, Set


@dataclass(frozen=True)
class MainStageConfig:
    """Fixed main onboarding stage definition."""

    id: str
    label: str
    order: int


FIXED_MAIN_STAGES: List[MainStageConfig] = [
    MainStageConfig(
        id="resource_fulfilment_to_identification",
        label="Resource Fulfilment to Identification",
        order=1,
    ),
    MainStageConfig(
        id="identification_to_onboarding",
        label="Identification to Onboarding",
        order=2,
    ),
    MainStageConfig(
        id="onboarding_to_billing",
        label="Onboarding to Billing",
        order=3,
    ),
]

VALID_MAIN_STAGE_IDS: Set[str] = {stage.id for stage in FIXED_MAIN_STAGES}
MAIN_STAGE_BY_ID = {stage.id: stage for stage in FIXED_MAIN_STAGES}
