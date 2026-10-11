"""API endpoints for persisted onboarding SLA datasets."""

from contextlib import asynccontextmanager
import tempfile
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from Agents.ExcelAnalyst.agent import run_excel_analyst_async
from Backend.calculations import calculate_dataset, calculate_focus_area, calculate_partners_list, calculate_pipeline, calculate_team_comparison
from Backend.calculations.normalization import normalize_dataframe
from Backend.db import repository as repo
from Backend.db.migrate import upgrade_to_head
from Backend.db.repository import LoadedDataset
from Backend.db.session import init_db, session_scope
from Backend.records.service import RecordNotFound, RecordValidationError, add_partner, get_rows_payload, get_schema_payload, update_partner
from Backend.records.validation import M_SUMMARY

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
AgentRunner = Callable[[str], Awaitable[Dict[str, Any]]]
NO_DATASET_MESSAGE = "No dataset is loaded. Upload a CSV first."

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db(); upgrade_to_head(); yield

app = FastAPI(title="Onboarding SLA Dashboard API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class PartnerPayload(BaseModel):
    fields: dict[str, Any]

async def _run_agent(file_path: str) -> Dict[str, Any]:
    return await run_excel_analyst_async(file_path=file_path)

def _active_loaded() -> LoadedDataset:
    try:
        with session_scope() as session: return repo.load_active(session)
    except repo.NoActiveDataset as exc: raise HTTPException(404, NO_DATASET_MESSAGE) from exc

async def process_csv_upload(upload: UploadFile, agent_runner: AgentRunner = _run_agent) -> Dict[str, Any]:
    if not upload.filename or Path(upload.filename).suffix.lower() != ".csv": raise HTTPException(400, "Upload a CSV file.")
    contents = await upload.read()
    if not contents: raise HTTPException(400, "The uploaded CSV is empty.")
    if len(contents) > MAX_UPLOAD_SIZE_BYTES: raise HTTPException(413, "The CSV must be 10 MB or smaller.")
    temporary_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temporary_file:
            temporary_file.write(contents); temporary_path = temporary_file.name
        agent_response = await agent_runner(temporary_path)
        dataframe = normalize_dataframe(pd.read_csv(temporary_path, encoding="utf-8-sig"))
        calculations = calculate_dataset(dataframe, agent_response)
        with repo.WRITE_LOCK:
            with session_scope() as session: repo.create_dataset(session, upload.filename, dataframe, agent_response)
        return {"agent": agent_response, "calculations": calculations}
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(422, str(exc)) from exc
    except HTTPException: raise
    except Exception as exc: raise HTTPException(500, "ExcelAnalyst could not process the uploaded CSV.") from exc
    finally:
        if temporary_path: Path(temporary_path).unlink(missing_ok=True)
        await upload.close()

@app.post("/api/uploads/csv")
@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)) -> Dict[str, Any]: return await process_csv_upload(file)

def _current_calculations(request: Request) -> Dict[str, Any]:
    loaded = _active_loaded(); filters = {key: value for key, value in request.query_params.items() if value}
    return calculate_dataset(loaded.dataframe, loaded.agent_response, filters)

@app.get("/api/calculations")
def get_calculations(request: Request) -> Dict[str, Any]: return _current_calculations(request)
@app.get("/api/summary")
def get_summary(request: Request) -> Dict[str, Any]:
    loaded = _active_loaded(); calculations = _current_calculations(request); kpis = calculations["kpis"]
    calculations["kpis"] = {**kpis, "totalCandidates": kpis["totalRecords"], "projectGroups": kpis["groupCount"], "avgTotalOnboardingDays": kpis["averageTotalDuration"], "minTotalOnboardingDays": kpis["minimumTotalDuration"], "maxTotalOnboardingDays": kpis["maximumTotalDuration"]}
    calculations["groupColumn"] = calculations["configuration"]["groupColumn"]; calculations["dataset"] = {"filename": loaded.filename}; return calculations
@app.get("/api/pipeline")
def get_pipeline(request: Request) -> Dict[str, Any]:
    loaded = _active_loaded(); return calculate_pipeline(loaded.dataframe, loaded.agent_response, {key: value for key, value in request.query_params.items() if value})
@app.get("/api/team-comparison")
def get_team_comparison(stage: str | None = None) -> Dict[str, Any]:
    loaded = _active_loaded()
    try: return calculate_team_comparison(loaded.dataframe, loaded.agent_response, stage_label=stage)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
@app.get("/api/focus-area")
def get_focus_area() -> Dict[str, Any]:
    loaded = _active_loaded()
    try: return calculate_focus_area(loaded.dataframe, loaded.agent_response)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
@app.get("/api/partners/schema")
def get_partner_schema() -> dict:
    try: return get_schema_payload()
    except repo.NoActiveDataset as exc: raise HTTPException(404, NO_DATASET_MESSAGE) from exc
@app.get("/api/partners/rows")
def get_partner_rows() -> dict:
    try: return get_rows_payload()
    except repo.NoActiveDataset as exc: raise HTTPException(404, NO_DATASET_MESSAGE) from exc
@app.post("/api/partners", status_code=201)
def post_partner(payload: PartnerPayload) -> dict:
    try: return add_partner(payload.fields)
    except repo.NoActiveDataset as exc: raise HTTPException(404, NO_DATASET_MESSAGE) from exc
    except RecordValidationError as exc: raise HTTPException(422, {"message": M_SUMMARY, "fieldErrors": exc.field_errors}) from exc
@app.patch("/api/partners/{row_id}")
def patch_partner(row_id: int, payload: PartnerPayload) -> dict:
    try: return update_partner(row_id, payload.fields)
    except repo.NoActiveDataset as exc: raise HTTPException(404, NO_DATASET_MESSAGE) from exc
    except RecordNotFound as exc: raise HTTPException(404, "Partner not found.") from exc
    except RecordValidationError as exc: raise HTTPException(422, {"message": M_SUMMARY, "fieldErrors": exc.field_errors}) from exc
@app.get("/api/partners")
def get_partners() -> Dict[str, Any]:
    loaded = _active_loaded()
    try: return calculate_partners_list(loaded.dataframe, loaded.agent_response)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
@app.get("/api/candidates")
def get_candidates(request: Request) -> Dict[str, Any]:
    loaded = _active_loaded(); return {"columns": list(loaded.dataframe.columns), "rows": _current_calculations(request)["records"]}
@app.get("/api/dataset-info")
def get_dataset_info() -> Dict[str, Any]:
    loaded = _active_loaded(); return {"filename": loaded.filename, "rowCount": int(len(loaded.dataframe))}
@app.get("/api/health")
def health_check() -> Dict[str, str]: return {"status": "ok"}
