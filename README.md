# Generic Onboarding SLA Dashboard

Local-first learning project for converting dynamic onboarding spreadsheets into
a confirmed, stable configuration that a deterministic backend can calculate.

## Current agent structure

- `Agents/ExcelAnalyst/data_cleaner.py` cleans spreadsheet values safely.
- `Agents/ExcelAnalyst/tools.py` reads CSV/Excel files and extracts metadata.
- `Agents/ExcelAnalyst/schemas.py` defines the reviewable configuration contract.
- `Agents/ExcelAnalyst/prompts.py` contains LLM instructions.
- `Agents/ExcelAnalyst/agent.py` creates and runs the Google ADK agent.

## Local verification

```bash
.venv/bin/python -m py_compile Agents/ExcelAnalyst/*.py
.venv/bin/python -c "from Agents.ExcelAnalyst.tools import inspect_spreadsheet; print(inspect_spreadsheet('Data/test_samples/candidate_standard.csv')['total_rows'])"
```

The agent needs `GEMINI_API_KEY` or `GOOGLE_API_KEY` in `.env` only when
running the Gemini interpretation step. Spreadsheet inspection and cleaning
run locally.

## CSV requirements

- CSV dates must be calendar-valid `YYYY-MM-DD` (preferred) or `YYYY/MM/DD`.
The inspector rejects every other date representation, including ambiguous
values such as `06/06/2006`, before cleaning or agent analysis begins.

- One stage should have start and end date. Example : Mac setup start date and Mac setup end date. This will not let agent to assume.

## Upload prototype

Start the API from the project root:

```bash
cd /Users/manish/Documents/Development/Onboarding_agentic_dashboard
.venv/bin/python -m uvicorn Backend.main:app --reload
```

Wait until the terminal prints `Application startup complete`, then keep it
running. The API is available at `http://127.0.0.1:8000` and its health check
is `http://127.0.0.1:8000/api/health`.

Start the React app in a second terminal:

```bash
cd /Users/manish/Documents/Development/Onboarding_agentic_dashboard/FrontEnd
npm run dev
```

Open the URL Vite prints, normally `http://localhost:5173`. The React app
proxies `/api` requests to the backend, so both terminals must remain running
while you upload a CSV.

If the UI reports that the API cannot be reached, first open
`http://127.0.0.1:8000/api/health`. It should return:

```json
{"status":"ok"}
```

For an agent-processing error, check the backend terminal. The API returns a
JSON error message after the agent finishes or fails; it does not require the
frontend to wait through a separate polling step.

## Database

The default database is SQLite at `Data/workspace/onboarding.db`. Set
`DATABASE_URL` to use another SQLAlchemy-compatible database URL. Run
`.venv/bin/alembic upgrade head` to migrate it; API startup runs this migration
automatically. Re-uploading creates a new active dataset and retains older
datasets in the database as inactive history.

## Manage partners

Open `/partners/manage` after uploading a CSV to add or edit partners. The
dashboard recalculates from the persisted dataset after every saved change.

## Generic calculation engine

The backend calculation engine is deliberately independent of source headers.
After `ExcelAnalyst` maps the identifier, optional group and completion fields,
and ordered stages, the API returns calculations derived from those mappings.

- A stage uses its mapped numeric duration field when present; otherwise its
  mapped ISO start/end dates determine elapsed days.
- Per-stage metrics: average, sample standard deviation, minimum, maximum,
  tracked count, and an anomaly cutoff of `average + 1 × standard deviation`.
- Anomalies exceed that cutoff. Incomplete records become focus areas from
  75% of the stage average through the cutoff.
- Per-group averages and deviations from the global stage average, dynamic
  categorical filters, record-level stage trends, and current-stage forecasts
  are calculated in the backend.
- Invalid numeric values, invalid/negative dates, values above 365 days,
  missing data, zero averages, and duplicate normalized headers are handled
  without frontend calculation logic.

`POST /api/uploads/csv` (and the compatibility alias `POST /api/upload`) now
returns both the agent mapping and a `calculations` object. For an uploaded
dataset, `GET /api/calculations`, `GET /api/summary`, `GET /api/candidates`,
and `GET /api/dataset-info` expose the generic calculated result.
