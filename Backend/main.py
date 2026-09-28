"""Prototype API endpoint for uploading a CSV to ExcelAnalyst."""

import tempfile
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from Agents.ExcelAnalyst.agent import run_excel_analyst_async


MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
AgentRunner = Callable[[str], Awaitable[Dict[str, Any]]]

app = FastAPI(title="Onboarding SLA Dashboard API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["POST"],
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

    temporary_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temporary_file:
            temporary_file.write(contents)
            temporary_path = temporary_file.name
        return await agent_runner(temporary_path)
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
async def upload_csv(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload a CSV and wait for the ExcelAnalyst JSON response."""
    return await process_csv_upload(file)


@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """Small readiness endpoint for local development."""
    return {"status": "ok"}
