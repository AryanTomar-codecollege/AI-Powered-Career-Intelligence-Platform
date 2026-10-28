# CareerCast

This starter implements only the first requested modules: **Supabase authentication, structured user profile, and NLP resume parsing**. It follows the PDF's Week 1–2 emphasis on a validated profile form and a spaCy-based resume parser for skills, roles, and education signals. It does **not** implement career prediction yet.

## Stack

- Frontend: plain HTML, CSS, JavaScript, Supabase JS v2.
- Backend: FastAPI, SQLAlchemy 2, Pydantic settings.
- Authentication: Supabase Auth; backend checks the access token against Supabase's `/auth/v1/user` endpoint.
- Database: SQLite by default for local development; PostgreSQL is supported through `DATABASE_URL`.
- Resume parsing: PyMuPDF for PDF, python-docx for DOCX, spaCy NER when the English model is installed, plus an editable phrase-matching vocabulary for technical skills/titles.

## 1. Requirements

Use Python 3.11 or 3.12. Create a virtual environment in the project root.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
Copy-Item .env.example .env
Copy-Item frontend\config.js.example frontend\config.js
```

If PowerShell blocks activation, use `Set-ExecutionPolicy -Scope Process Bypass` for that terminal only, then activate again.

### macOS / Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env
cp frontend/config.js.example frontend/config.js
```

If spaCy's model download is unavailable, the parser still runs using the built-in keyword matcher, but institution NER coverage is reduced.

## 2. Configure Supabase

1. Create/open a project in Supabase.
2. In **Project Settings → API**, copy the project URL and the public **publishable/anon** key.
3. Put them in both `.env` and `frontend/config.js`:
   - `.env`: `SUPABASE_URL`, `SUPABASE_ANON_KEY`
   - `frontend/config.js`: `SUPABASE_URL`, `SUPABASE_ANON_KEY`
4. Never use a `service_role` key or secret key in browser code.
5. In Supabase Authentication settings, configure the site URL and allowed redirect URLs for your local frontend. This starter uses email/password authentication. If email confirmation is enabled, the user must confirm the email before signing in.
6. Ensure the frontend origin in `.env` matches the address used to open the page. For the commands below it is `http://127.0.0.1:5500`.

## 3. Run the app

Open two terminals from the project root.

**Terminal 1 — backend**
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 — frontend**
```powershell
cd frontend
python -m http.server 5500 --bind 127.0.0.1
```

Open `http://127.0.0.1:5500`. API docs: `http://127.0.0.1:8000/docs`. Health check: `http://127.0.0.1:8000/health`.

Do not open `index.html` with `file://`; use the local HTTP server so browser configuration and CORS behave predictably.

## 4. API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Basic health check |
| GET | `/api/profile` | Get/create the signed-in user's profile |
| PUT | `/api/profile` | Validate and update profile fields |
| POST | `/api/resumes/parse` | Upload PDF/DOCX and parse it |
| GET | `/api/resumes` | List the current user's parsed resumes |

All `/api` endpoints require `Authorization: Bearer <Supabase access token>`. A user can only access their own profile and resumes. The backend obtains identity from Supabase rather than trusting a user ID supplied by the browser.

## 5. Database and resume handling

- SQLite database file `careercast.db` is created on first backend startup and is intentionally ignored by Git.
- To use PostgreSQL, install the included psycopg dependency and set, for example, `DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME`.
- Resume contents and extracted text are stored in the database. Tell users this before production use, restrict database access, and define a retention/deletion policy.
- Duplicate uploads with identical content for the same profile return HTTP 409.
- Only PDF and DOCX are accepted; upload limit is controlled by `MAX_RESUME_SIZE_MB`.
- Scanned/image-only PDFs are rejected with a helpful message because OCR is not included.
- The current skill and title vocabulary is a baseline, not a comprehensive taxonomy. Extend `app/resume_parser.py` and evaluate against labeled resumes to measure precision/recall.

## 6. Current scope and known limits

- Supabase handles account creation, sign-in, sessions, and sign-out. The database stores the app profile keyed by the Supabase user ID.
- The parser combines spaCy general-purpose NER with phrase matching because generic NER models do not reliably identify technical skills.
- Education extraction currently returns detected institution names and recognized education terms in the same output field; this is a baseline signal extractor, not a fully normalized education-history parser.
- Mixed-language resumes, synonym resolution, OCR, file malware scanning, password reset, rate limiting, and production observability are not included.
- The PDF's ≥90% parser precision target must be measured on the specified held-out dataset; this starter does not claim that target has already been met.
- The PDF's later career classifier, recommendations, skill-gap engine, MLflow registry, CLI, and optional Streamlit dashboard are intentionally out of scope for this first delivery.

## 7. Before deployment

Use PostgreSQL, configure HTTPS and production CORS origins, add database migrations (Alembic), rate limiting, structured logging, tests, upload scanning, backup/retention policies, and a verified deployment secret store. Do not commit `.env`, `frontend/config.js`, user resumes, or database files.
