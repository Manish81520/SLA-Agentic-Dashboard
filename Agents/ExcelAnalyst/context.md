# ExcelAnalyst Agent Context

Use this file as the working brief for ExcelAnalyst. It describes what the agent owns, what it must not do, and how its output is consumed.

## Purpose

ExcelAnalyst interprets an onboarding spreadsheet (CSV or Excel) whose headers and stages are not known in advance. It produces a reviewable `DatasetUnderstanding` mapping. Deterministic backend code then calculates SLA metrics from those mappings.

This is a local-first learning project. Do not add cloud deployment, CI/CD, or change the Gemini model unless explicitly requested. The model is `gemini-2.5-flash`.

## Separation of concerns

| Layer | Files | Owns |
| --- | --- | --- |
| Cleaning | `data_cleaner.py` | Mechanical, generic cleaning only. No LLM. No column-name or stage-name assumptions. |
| Inspection | `tools.py` | Read CSV/Excel, validate CSV dates, clean, extract metadata for the LLM. |
| Contract | `schemas.py` | Stable Pydantic output: `DatasetUnderstanding`. |
| Instructions | `prompts.py` | LLM instructions only. |
| ADK runtime | `agent.py` | Agent construction and execution. Does not attach LLM tools; inspection runs in Python first. |
| Calculations | `Backend/calculations/` | SLA math, anomalies, pipeline roll-up, filters. Never the agent. |

The agent never calculates averages, flags numeric anomalies, or invents headers. Every `ColumnMapping.column` must be an exact cleaned source header from inspection metadata (`column_names`).

## Runtime flow

1. Caller provides a file path, or inspection searches `Data/` for the first `.csv` / `.xlsx` / `.xls`.
2. `inspect_spreadsheet` reads the file with pandas.
3. **CSV only:** date cells that look like dates (header keyword or value pattern) must be calendar-valid `YYYY-MM-DD` (preferred) or `YYYY/MM/DD`. Any other representation fails immediately with `date_format_validation.issues`. The file is not cleaned or sent to the LLM.
4. `clean_dataframe` strips headers and cells, normalizes null-like tokens (`NA`, `N/A`, `-`, empty, etc.), drops empty and duplicate rows, and canonicalizes already-valid ISO dates to `YYYY-MM-DD`. It never infers day-first vs month-first.
5. Numeric columns (80%+ of populated values coerce to numbers) are never treated as dates, even if the header contains “date”. This protects duration/SLA fields such as `SLA Start Date`.
6. Inspection JSON (column names, dtypes, samples, null stats, potential date flags, preview rows, `cleaning_report`) is passed to the ADK agent.
7. The agent returns structured `DatasetUnderstanding`. `agent.py` parses JSON (including fenced code blocks).
8. `Backend/calculations/configuration.py` translates mappings into `CalculationConfiguration`. Stage order is the agent’s order. `project_mapping` becomes the group column. `main_stage_mapping.stage_id` must be one of the three fixed pipeline IDs.

API path: `POST /api/uploads/csv` (alias `POST /api/upload`) writes a temp CSV, runs `run_excel_analyst_async`, then `calculate_dataset`. Requires `GEMINI_API_KEY` or `GOOGLE_API_KEY` for the Gemini step. Inspection and cleaning run without a key.

## Output contract (`DatasetUnderstanding`)

Required/core mappings:

- `identifier_mapping` — primary record id
- `partner_name_mapping` — human-readable partner/person name when present
- `project_mapping` — project / team / account grouping when present
- `detected_project_name` — names seen in headers or samples
- `onboarding_start_mapping` / `onboarding_completion_mapping` — overall dates
- `stages[]` — substages in logical chronological order, each with:
  - `start_mapping`, `end_mapping`, optional `duration_mapping`
  - `main_stage_mapping` with `stage_id`, `confidence`, `rationale`
- `date_column_mappings` — every date/timestamp column
- `date_format_ambiguities` — ambiguous formats; do not silently pick DD/MM vs MM/DD
- `columns_requiring_confirmation` — anything too uncertain to calculate on

Each mapping: `column` (exact cleaned header or null), `confidence` 0.0–1.0, `rationale` grounded only in supplied metadata.

If no reliable column exists, set `column` to null, use low confidence, and add a confirmation entry.

## Fixed main pipeline stages

Every detected substage maps to exactly one of:

1. `resource_fulfilment_to_identification` — sourcing, resourcing requests, candidate identification, initial screening, requirements initiation
2. `identification_to_onboarding` — interviews, offer/acceptance, BGV, KYC, compliance, documentation, pre-onboarding verification
3. `onboarding_to_billing` — asset/laptop allocation, access/account provisioning, MAC/IT setup, project induction, KT, billing readiness

If assignment is unreliable: `stage_id` null, confidence below 0.5, plus a `columns_requiring_confirmation` item.

## Hard rules

- Preserve exact cleaned source headers in all mappings. Never invent or “normalize” a new name for the LLM output.
- Do not treat numeric SLA/duration values as dates based only on the header.
- Require human confirmation for uncertain mappings and ambiguous date formats.
- CSV dates are not inferred from values. If inspection reports a CSV date-validation error, do not analyze or map the file; tell the user to fix the CSV and resubmit.
- Prefer stages that have explicit start and end date columns (example: Mac setup start date and Mac setup end date) so the agent does not guess a single-column stage.
- Excel date ambiguity is recorded in `date_format_ambiguities`; CSV invalid dates never reach the agent.

## How backend uses the mapping

- Stage duration: use mapped numeric duration when present; otherwise elapsed days from mapped ISO start/end.
- Per-stage metrics: average, sample standard deviation, min, max, tracked count, anomaly cutoff `average + 1 × std`.
- Incomplete records can become focus areas from 75% of stage average through the cutoff.
- Pipeline API (`GET /api/pipeline`) rolls substages into the three fixed main stages using `main_stage_mapping`.
- Invalid numbers, invalid/negative dates, values above 365 days, missing data, and duplicate normalized headers are handled in the engine, not the frontend.

## Local verification

```bash
.venv/bin/python -m py_compile Agents/ExcelAnalyst/*.py
.venv/bin/python -c "from Agents.ExcelAnalyst.tools import inspect_spreadsheet; print(inspect_spreadsheet('Data/test_samples/candidate_standard.csv')['total_rows'])"
```

Fixtures in `Data/test_samples/`:

- `candidate_standard.csv` — clear candidate lifecycle, ISO dates
- `partner_alternative_headers.csv` — different entity and headers
- `ambiguous_date_formats.csv` — ISO-normalized date-stage fixture
- `incomplete_mappings.csv` — missing completion fields that need confirmation

## File map

```
Agents/ExcelAnalyst/
  agent.py          # create_excel_analyst_agent, run_excel_analyst(_async)
  prompts.py        # EXCEL_ANALYST_INSTRUCTION
  schemas.py        # DatasetUnderstanding and nested models
  tools.py          # inspect_spreadsheet, CSV date validation
  data_cleaner.py   # clean_dataframe, is_supported_iso_date
  context.md        # this brief
```
