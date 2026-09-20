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
.venv/bin/python -c "from Agents.ExcelAnalyst.tools import inspect_spreadsheet; print(inspect_spreadsheet()['total_rows'])"
```

The agent needs `GEMINI_API_KEY` or `GOOGLE_API_KEY` in `.env` only when
running the Gemini interpretation step. Spreadsheet inspection and cleaning
run locally.
