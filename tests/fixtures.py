"""Shared fixtures for persistence-layer tests."""

import pandas as pd

from Backend.db.session import init_db


AGENT_MAPPING = {
    "identifier_mapping": {"column": "Worker ID"},
    "partner_name_mapping": {"column": "Partner Name"},
    "project_mapping": {"column": "Delivery Team"},
    "onboarding_start_mapping": {"column": "Request Date"},
    "onboarding_completion_mapping": {"column": "Completion Date"},
    "stages": [
        {"stage_name": "Verification", "duration_mapping": {"column": "Verification SLA"}, "start_mapping": {"column": "Verification Start"}, "end_mapping": {"column": "Verification End"}},
        {"stage_name": "Provisioning", "duration_mapping": None, "start_mapping": {"column": "Provisioning Start"}, "end_mapping": {"column": "Provisioning End"}},
    ],
}


def make_dataframe() -> pd.DataFrame:
    """Return the standard three-row onboarding sample."""
    return pd.DataFrame({
        "Worker ID": ["W-1", "W-2", "W-3"], "Partner Name": ["Ava Patel", "Noah Smith", "Mia Chen"],
        "Delivery Team": ["Alpha", "Alpha", "Beta"], "Request Date": ["2026-01-01"] * 3,
        "Completion Date": ["2026-01-10", "", "2026-01-09"], "Verification SLA": [2, 4, 8],
        "Verification Start": ["2026-01-01"] * 3, "Verification End": ["2026-01-03", "2026-01-05", "2026-01-09"],
        "Provisioning Start": ["2026-01-03", "2026-01-05", "2026-01-09"], "Provisioning End": ["2026-01-05", "2026-01-08", "2026-01-13"],
        "Optional Field": [None, "available", None],
    })


def fresh_db() -> None:
    """Initialize an isolated in-memory persistence database."""
    init_db("sqlite://", create_tables=True)
