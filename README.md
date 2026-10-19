# Generic Onboarding SLA Dashboard

A local-first dashboard that turns any onboarding spreadsheet (CSV) into SLA metrics, anomaly alerts, and a stage pipeline view, without project-specific code.

**How it works**

```
CSV upload -> FastAPI backend -> ExcelAnalyst agent (Gemini via Google ADK) -> column/stage mapping
           -> deterministic calculation engine -> SQL database -> React dashboard
```

| Layer | Responsibility |
|---|---|
| Agent (`Agents/ExcelAnalyst/`) | Understands the spreadsheet structure and returns a mapping. Never does math. |
| Backend (`Backend/`) | Cleans, calculates (averages, anomalies, pipeline), persists, serves the API. |
| Frontend (`FrontEnd/`) | Renders what the backend returns. No calculations. |

For architecture details, API reference, and calculation rules, see [AI_CONTEXT.md](AI_CONTEXT.md) and [AGENTS.md](AGENTS.md).

---

## 1. Prerequisites

Install these on the new laptop first.

| Tool | Required version | Check with |
|---|---|---|
| Git | any recent | `git --version` |
| Python | **3.11 or newer** | `python3 --version` |
| Node.js | **20.19+ or 22.12+** (required by Vite 7) | `node --version` |
| npm | comes with Node | `npm --version` |
| Gemini API key | free key from [Google AI Studio](https://aistudio.google.com/apikey) | n/a |

### Installing the prerequisites

**macOS (Homebrew)**
```bash
brew install git python@3.12 node
```

**Windows (winget, in PowerShell)**
```powershell
winget install Git.Git
winget install Python.Python.3.12
winget install OpenJS.NodeJS.LTS
```
Close and reopen the terminal afterwards so `python` and `node` are on the PATH.

**Ubuntu / Debian**
```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip
# Node: use nvm or NodeSource to get 20.19+ / 22.12+ (apt's default is often too old)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
# restart the terminal, then:
nvm install 22
```

No database server is needed. The app uses SQLite by default.

---

## 2. Get the code

```bash
git clone <your-repo-url> Onboarding_agentic_dashboard
cd Onboarding_agentic_dashboard
```

All backend commands below run from this project root.

---

## 3. Backend setup

### 3.1 Create a virtual environment

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
If PowerShell blocks the script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

### 3.2 Install Python dependencies

These are the exact versions pinned in `pyproject.toml`:

```bash
pip install --upgrade pip
pip install \
  alembic==1.20.0 \
  fastapi==0.141.1 \
  google-adk==2.9.1 \
  google-genai==2.24.0 \
  openpyxl==3.1.5 \
  pandas==3.0.6 \
  pydantic==2.13.5 \
  python-dotenv==1.2.3 \
  python-multipart==0.0.22 \
  sqlalchemy==2.1.4 \
  uvicorn==0.53.0
```

On Windows PowerShell, put it on one line (replace each trailing `\` with a space) or use the backtick `` ` `` as the line continuation character.

> Note: `pip install .` does not work for this repo, because it has several top-level folders and no build configuration. Use the explicit install above.

### 3.3 Configure environment variables

Create a file named `.env` in the project root (it is git-ignored):

```env
GEMINI_API_KEY=your-key-here
GOOGLE_GENAI_USE_VERTEXAI=FALSE
```

| Variable | Required | Purpose |
|---|---|---|
| `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) | Yes, for uploads | Used by the ExcelAnalyst agent (`gemini-2.5-flash`). |
| `GOOGLE_GENAI_USE_VERTEXAI` | Recommended `FALSE` | Uses the AI Studio key instead of Vertex AI. |
| `DATABASE_URL` | No | Any SQLAlchemy URL. Defaults to SQLite at `Data/workspace/onboarding.db`. |

Never commit `.env`.

### 3.4 Agent setup (Google ADK + Gemini)

The ExcelAnalyst agent is built with [Google ADK](https://google.github.io/adk-docs/) and runs **inside the backend process**. There is no separate agent server and no `adk` CLI step. Everything it needs is installed by the `pip install` in 3.2:

| Package | Role |
|---|---|
| `google-adk` | Agent framework (`Agent`, `Runner`, `InMemorySessionService`) |
| `google-genai` | Gemini client used by ADK |
| `pydantic` | Structured output contract (`DatasetUnderstanding`) |
| `python-dotenv` | Loads `GEMINI_API_KEY` from `.env` |
| `pandas`, `openpyxl` | Spreadsheet reading and cleaning before the agent sees the data |

The model is `gemini-2.5-flash`. Do not change it unless you intend to.

**Step 1: Get a Gemini API key**

1. Go to <https://aistudio.google.com/apikey> and sign in with a Google account.
2. Click **Create API key** and copy it.
3. Put it in `.env` in the project root (see 3.3):
   ```env
   GEMINI_API_KEY=your-key-here
   GOOGLE_GENAI_USE_VERTEXAI=FALSE
   ```

**Step 2: Verify ADK is installed**

```bash
pip show google-adk google-genai
python -c "import google.adk, google.genai; print('ADK OK')"
```

**Step 3: Verify the inspection step (no API key needed)**

This runs the cleaning and metadata extraction that happens before the agent is called:

```bash
python -c "from Agents.ExcelAnalyst.tools import inspect_spreadsheet; print(inspect_spreadsheet('Data/test_samples/candidate_standard.csv')['total_rows'])"
```

Expected output: `3`.

**Step 4: Verify the Gemini key works**

```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); from google import genai; c = genai.Client(api_key=os.environ['GEMINI_API_KEY']); print(c.models.generate_content(model='gemini-2.5-flash', contents='Reply with OK').text)"
```

Expected output: a short reply such as `OK`. A 400/403 error means the key is wrong; a 429 means the free-tier rate limit was hit, so wait a minute.

**Step 5: Run the agent on its own (optional, no frontend needed)**

```bash
python Agents/ExcelAnalyst/agent.py
```

Without a key this prints a short inspection summary of the first CSV in `Data/`. With a key it prints the full `DatasetUnderstanding` JSON (identifier, partner name, project, stages, main-stage mapping, confirmation items). To run it on a specific file:

```bash
python -c "from Agents.ExcelAnalyst.agent import run_excel_analyst; import json; print(json.dumps(run_excel_analyst('Data/test_samples/partner_alternative_headers.csv'), indent=2))"
```

The agent only interprets structure. It never calculates averages or SLAs; the backend does that after it returns.

### 3.5 Database

Nothing to do. On startup the API creates the database folder and runs the Alembic migrations automatically. To run them manually:

```bash
alembic upgrade head
```

### 3.6 Start the API

```bash
python -m uvicorn Backend.main:app --reload
```

Wait for `Application startup complete`. Verify: open <http://127.0.0.1:8000/api/health>, which should return `{"status":"ok"}`. Interactive API docs are at <http://127.0.0.1:8000/docs>.

Keep this terminal running.

---

## 4. Frontend setup

Open a **second terminal**:

```bash
cd FrontEnd
npm install
npm run dev
```

Open the URL Vite prints, normally <http://localhost:5173>. The dev server proxies `/api` to `http://127.0.0.1:8000`, so both terminals must stay running.

Production build check:
```bash
npm run build
```

---

## 5. First run

1. Open <http://localhost:5173>. The dashboard shows an empty state.
2. Click **Upload CSV** and choose `Data/onboarding.csv`.
3. Wait for the analysis (a few seconds while Gemini maps the columns).
4. The dashboard then shows KPI cards, the 3-stage pipeline, team comparison, focus area, and the partners list.
5. Use **Manage** to add or edit partners; the dashboard recalculates after each save.

Other sample files are in `Data/test_samples/` (different headers, incomplete mappings, etc.).

---

## 6. CSV requirements

- Format: `.csv`, UTF-8, up to 10 MB.
- **Dates must be `YYYY-MM-DD` (preferred) or `YYYY/MM/DD`.** Any other format (for example `06/06/2006`) is rejected before analysis.
- Each partner should have a **unique identifier**. Duplicate identifiers reject the upload.
- Give each stage a **start date and an end date** column (for example `MAC Set up Start Date` and `MAC Set up Completed`) so the agent does not have to guess.
- Numeric SLA/duration columns are never treated as dates, even if the header contains "date".

---

## 7. Running the tests

From the project root with the virtual environment active:

```bash
python -m unittest discover tests
```

Syntax check:
```bash
python -m compileall Agents Backend
```

Tests use an in-memory database and a fake agent, so they need no API key or network access.

---

## 8. Project structure

```
Agents/ExcelAnalyst/   Agent: cleaning, inspection tools, prompts, schemas, ADK runner
Backend/
  main.py              FastAPI app and routes
  calculations/        Deterministic SLA/anomaly/pipeline engine
  db/                  SQLAlchemy models, sessions, repository, Alembic migrations
  records/             Partner schema, validation, add/edit service
FrontEnd/              React + Vite app (plain CSS, Geist font)
Data/                  Sample CSVs (onboarding.csv, test_samples/)
tests/                 Unit and API tests
alembic.ini            Migration config
pyproject.toml         Python version and pinned dependencies
```

---

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| UI says "The API could not be reached" | Backend isn't running. Start it and check `/api/health`. |
| `GEMINI_API_KEY or GOOGLE_API_KEY environment variable is missing` | Create `.env` in the project root (not in `FrontEnd/`) and restart uvicorn. |
| `ModuleNotFoundError: Backend` or `Agents` | Run commands from the project root, with the virtual environment active. |
| Upload fails with a date validation message | Convert all dates in the CSV to `YYYY-MM-DD`. |
| Upload fails with "Duplicate identifiers found" | Make the identifier column unique in the CSV. |
| Gemini 429 / quota error | Free-tier rate limit. Wait a minute and retry. |
| `ModuleNotFoundError: google.adk` | Virtual environment not active, or step 3.2 was skipped. Activate `.venv` and rerun the `pip install`. |
| Gemini 400/403 "API key not valid" | Re-copy the key from AI Studio into `.env` with no quotes or spaces, then restart uvicorn. |
| ADK tries to use Vertex AI / asks for a project | Set `GOOGLE_GENAI_USE_VERTEXAI=FALSE` in `.env`. |
| `python Agents/ExcelAnalyst/agent.py` only prints a summary | No API key was found. That is expected without a key. |
| `npm install` or Vite fails on engine version | Upgrade Node to 20.19+ or 22.12+. |
| Port 8000 or 5173 already in use | Stop the other process, or run uvicorn with `--port 8001` and update the proxy in `FrontEnd/vite.config.js`. |
| Stale data after a bad upload | Stop the API and delete `Data/workspace/onboarding.db`; it is recreated on startup. |

---

## 10. Data privacy note

Uploading a CSV sends column metadata, sample values, and preview rows (which may include names and emails) to the Gemini API. Do not upload real personal data unless your organization permits it for the Gemini tier you are using.

---

## 11. Scope

This is a local-first learning project. Cloud deployment, CI/CD, and changing the Gemini model are out of scope unless explicitly requested.