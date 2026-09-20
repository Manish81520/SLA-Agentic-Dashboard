"""
ExcelAnalyst Agent Module.

Provides:
- ExcelAnalyst Google ADK Agent
- Spreadsheet inspection tools (inspect_spreadsheet)
- Data schemas (DatasetUnderstanding, OnboardingStage, ColumnMapping,
  DateFormatAmbiguity, ConfirmationRequirement)
- Execution entrypoints (run_excel_analyst, run_excel_analyst_async)
"""

from typing import Any

__all__ = [
    "create_excel_analyst_agent",
    "run_excel_analyst",
    "run_excel_analyst_async",
    "inspect_spreadsheet",
    "DatasetUnderstanding",
    "OnboardingStage",
    "ColumnMapping",
    "DateFormatAmbiguity",
    "ConfirmationRequirement",
]

def __getattr__(name: str) -> Any:
    if name in ("DatasetUnderstanding", "OnboardingStage", "ColumnMapping", "DateFormatAmbiguity", "ConfirmationRequirement"):
        from . import schemas
        return getattr(schemas, name)
    if name in (
        "create_excel_analyst_agent",
        "run_excel_analyst",
        "run_excel_analyst_async",
    ):
        from . import agent
        return getattr(agent, name)
    if name == "inspect_spreadsheet":
        from . import tools
        return getattr(tools, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
