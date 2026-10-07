"""Prototype API endpoint for uploading a CSV to ExcelAnalyst."""

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from Agents.ExcelAnalyst.agent import run_excel_analyst_async
from Backend.calculations import calculate_dataset, calculate_pipeline, calculate_team_comparison


MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
AgentRunner = Callable[[str], Awaitable[Dict[str, Any]]]


@dataclass
class LoadedDataset:
    """In-memory source and mapping state for the active prototype dataset."""

    dataframe: pd.DataFrame
    agent_response: Dict[str, Any]
    filename: str


CURRENT_DATASET: LoadedDataset | None = None

app = FastAPI(title="Onboarding SLA Dashboard API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _run_agent(file_path: str) -> Dict[str, Any]:
    """Run ExcelAnalyst after the uploaded CSV has passed API validation."""
    return await run_excel_analyst_async(file_path=file_path)


async def process_csv_upload(
    upload: UploadFile,
    agent_runner: AgentRunner = _run_agent,
) -> Dict[str, Any]:
    """Persist one CSV temporarily, wait for ExcelAnalyst, and return its JSON."""
    if not upload.filename or Path(upload.filename).suffix.lower() != ".csv":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload a CSV file.")

    contents = await upload.read()
    if not contents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded CSV is empty.")
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="The CSV must be 10 MB or smaller.",
        )

    global CURRENT_DATASET
    temporary_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temporary_file:
            temporary_file.write(contents)
            temporary_path = temporary_file.name
        agent_response = await agent_runner(temporary_path)
        dataframe = pd.read_csv(temporary_path, encoding="utf-8-sig")
        calculations = calculate_dataset(dataframe, agent_response)
        CURRENT_DATASET = LoadedDataset(
            dataframe=dataframe,
            agent_response=agent_response,
            filename=upload.filename,
        )
        return {"agent": agent_response, "calculations": calculations}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ExcelAnalyst could not process the uploaded CSV.",
        ) from exc
    finally:
        if temporary_path:
            Path(temporary_path).unlink(missing_ok=True)
        await upload.close()


@app.post("/api/uploads/csv")
@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload a CSV, wait for ExcelAnalyst, and return generic calculations."""
    return await process_csv_upload(file)


def _current_calculations(request: Request) -> Dict[str, Any]:
    """Recalculate the active dataset for optional generic query filters."""
    if CURRENT_DATASET is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No dataset is loaded. Upload a CSV first.",
        )
    filters = {key: value for key, value in request.query_params.items() if value}
    return calculate_dataset(CURRENT_DATASET.dataframe, CURRENT_DATASET.agent_response, filters)


@app.get("/api/calculations")
async def get_calculations(request: Request) -> Dict[str, Any]:
    """Return the full generic calculation response for the active dataset."""
    return _current_calculations(request)


@app.get("/api/summary")
async def get_summary(request: Request) -> Dict[str, Any]:
    """Return a summary compatible with dashboard-style consumers."""
    calculations = _current_calculations(request)
    kpis = calculations["kpis"]
    calculations["kpis"] = {
        **kpis,
        "totalCandidates": kpis["totalRecords"],
        "projectGroups": kpis["groupCount"],
        "avgTotalOnboardingDays": kpis["averageTotalDuration"],
        "minTotalOnboardingDays": kpis["minimumTotalDuration"],
        "maxTotalOnboardingDays": kpis["maximumTotalDuration"],
    }
    calculations["groupColumn"] = calculations["configuration"]["groupColumn"]
    calculations["dataset"] = {"filename": CURRENT_DATASET.filename}
    return calculations


@app.get("/api/pipeline")
async def get_pipeline(request: Request) -> Dict[str, Any]:
    """Return the 3-step onboarding pipeline roll-up for the active dataset."""
    if CURRENT_DATASET is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No dataset is loaded. Upload a CSV first.",
        )
    filters = {key: value for key, value in request.query_params.items() if value}
    return calculate_pipeline(CURRENT_DATASET.dataframe, CURRENT_DATASET.agent_response, filters)


@app.get("/api/team-comparison")
async def get_team_comparison(stage: str | None = None) -> Dict[str, Any]:
    """Return backend-owned team averages and partner focus data for one stage."""
    if CURRENT_DATASET is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No dataset is loaded. Upload a CSV first.",
        )
    try:
        return calculate_team_comparison(
            CURRENT_DATASET.dataframe,
            CURRENT_DATASET.agent_response,
            stage_label=stage,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@app.get("/api/candidates")
async def get_candidates(request: Request) -> Dict[str, Any]:
    """Return generic record-level metrics for the active dataset."""
    calculations = _current_calculations(request)
    return {"columns": list(CURRENT_DATASET.dataframe.columns), "rows": calculations["records"]}


@app.get("/api/dataset-info")
async def get_dataset_info() -> Dict[str, Any]:
    """Identify the active in-memory dataset without exposing a local path."""
    if CURRENT_DATASET is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No dataset is loaded. Upload a CSV first.")
    return {"filename": CURRENT_DATASET.filename, "rowCount": int(len(CURRENT_DATASET.dataframe))}


@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """Small readiness endpoint for local development."""
    return {"status": "ok"}
