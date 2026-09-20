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

## CSV date requirement

CSV dates must be calendar-valid `YYYY-MM-DD` (preferred) or `YYYY/MM/DD`.
The inspector rejects every other date representation, including ambiguous
values such as `06/06/2006`, before cleaning or agent analysis begins.
