"""ADK construction and execution entrypoints for the ExcelAnalyst agent."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import find_dotenv, load_dotenv
from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

if __package__:
    from .prompts import EXCEL_ANALYST_INSTRUCTION
    from .schemas import (
        ColumnMapping,
        ConfirmationRequirement,
        DatasetUnderstanding,
        DateFormatAmbiguity,
        OnboardingStage,
    )
    from .tools import inspect_spreadsheet
else:
    # ``python agent.py`` adds only this file's directory to sys.path. Add
    # the repository root so the absolute package imports below can resolve.
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from Agents.ExcelAnalyst.prompts import EXCEL_ANALYST_INSTRUCTION
    from Agents.ExcelAnalyst.schemas import (
        ColumnMapping,
        ConfirmationRequirement,
        DatasetUnderstanding,
        DateFormatAmbiguity,
        OnboardingStage,
    )
    from Agents.ExcelAnalyst.tools import inspect_spreadsheet


load_dotenv(find_dotenv())


def create_excel_analyst_agent(model: str = "gemini-2.5-flash") -> Agent:
    """Create the structured-output ADK agent without attaching LLM tools."""
    return Agent(
        name="ExcelAnalyst",
        description="Interprets onboarding spreadsheet schemas dynamically.",
        model=model,
        instruction=EXCEL_ANALYST_INSTRUCTION,
        output_schema=DatasetUnderstanding,
    )


def _parse_agent_output(output: Any) -> Dict[str, Any]:
    """Return the final structured agent response as a dictionary."""
    if isinstance(output, dict):
        return output
    if not isinstance(output, str):
        return {"output": str(output)}

    cleaned = output.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"raw_text": output}


async def run_excel_analyst_async(
    file_path: Optional[str] = None,
    model: str = "gemini-2.5-flash",
) -> Dict[str, Any]:
    """Inspect a spreadsheet, then ask the agent for a reviewable configuration."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY or GOOGLE_API_KEY environment variable is missing.\n"
            "Export GEMINI_API_KEY before running the agent."
        )

    inspection = inspect_spreadsheet(file_path)
    if "error" in inspection:
        raise RuntimeError(f"Failed to inspect spreadsheet: {inspection['error']}")

    app_name = "onboarding_sla_dashboard"
    user_id = "analyst_user"
    session_id = "session_excel_analyst"
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )

    runner = Runner(
        agent=create_excel_analyst_agent(model=model),
        app_name=app_name,
        session_service=session_service,
    )
    prompt_text = (
        "Here is the extracted spreadsheet metadata as JSON:\n\n"
        f"{json.dumps(inspection, indent=2)}\n\n"
        "Analyze this metadata and return the DatasetUnderstanding structure."
    )
    user_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt_text)],
    )

    final_output = None
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_output = event.content.parts[0].text

    if final_output is None:
        raise RuntimeError("Agent completed without producing any output.")
    return _parse_agent_output(final_output)


def run_excel_analyst(
    file_path: Optional[str] = None,
    model: str = "gemini-2.5-flash",
) -> Dict[str, Any]:
    """Synchronous entrypoint for running ExcelAnalyst."""
    return asyncio.run(run_excel_analyst_async(file_path=file_path, model=model))


if __name__ == "__main__":
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        inspection = inspect_spreadsheet()
        print(json.dumps({
            "file_name": inspection.get("file_name"),
            "total_rows": inspection.get("total_rows"),
            "total_columns": inspection.get("total_columns"),
        }, indent=2))
        sys.exit(0)

    try:
        print(json.dumps(run_excel_analyst(), indent=2))
    except Exception as err:
        print(f"Error running ExcelAnalyst: {err}")
        sys.exit(1)
