# Skill Gap Analyzer & Course Recommender

An enterprise skill-gap analysis platform. Admins define role competency
matrices; employees upload a resume and receive an AI-driven readiness score,
per-category gap breakdown, and a personalized course learning path.

Built with a 7-stage RAG pipeline (resume parsing -> chunking -> embeddings ->
vector indexing -> semantic retrieval -> RAG context -> LLM analysis), followed
by a deterministic comparison engine and a two-stage course recommendation
pipeline. **Exactly two LLM calls per analysis.**

## Tech Stack

| Layer        | Technology                                             |
|--------------|--------------------------------------------------------|
| Frontend     | React (CRA), React Router, Axios, Lucide icons         |
| Backend      | FastAPI, Python 3.11+, Uvicorn                         |
| Database     | MongoDB Atlas (Motor async)                            |
| Vector Store | ChromaDB (persistent, in-process)                      |
| LLM          | Google Gemini (`gemini-2.0-flash`)                     |
| Embeddings   | sentence-transformers `all-MiniLM-L6-v2` (384-dim)     |
| RAG          | LangChain                                              |
| Parsing      | PyPDF2, python-docx                                    |

## Project Structure

```
skill-gap-analyzer/
  frontend/        React SPA
  backend/         FastAPI app, services, scripts
  setup.sh         One-command setup
  README.md
```

See the Detailed Design Document for the full architecture.

## Prerequisites

- Python 3.11+
- Node.js 18+
- A MongoDB Atlas connection string
- A Google Gemini API key

## Setup

1. **Configure environment variables**

   ```bash
   cp backend/.env.example backend/.env
   # edit backend/.env and fill in GEMINI_API_KEY and MONGODB_URI
   ```

   `frontend/.env` is already set to `REACT_APP_API_BASE_URL=http://localhost:8000/api/v1`.

2. **Run setup** (installs deps, generates 5000+ courses, embeds them)

   ```bash
   bash setup.sh
   ```

   On Windows without bash, run the equivalent steps manually:

   ```powershell
   cd backend
   pip install -r requirements.txt
   python scripts/generate_courses.py
   python scripts/embed_courses.py
   cd ../frontend
   npm install
   ```

## Running

**Terminal 1 - Backend**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend**
```bash
cd frontend
npm start
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- Health:   http://localhost:8000/api/v1/health

> On first backend start, the sentence-transformers model (`all-MiniLM-L6-v2`)
> is downloaded from HuggingFace, and the course embedding pipeline auto-runs if
> ChromaDB is behind MongoDB.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/generate_courses.py` | Generate dummy courses into MongoDB (`is_embedded=false`) across all categories. |
| `scripts/seed_roles.py`       | Seed a set of realistic default roles (idempotent — skips existing). |
| `scripts/embed_courses.py`    | Embed unembedded courses into ChromaDB. `--full-rebuild` to re-embed all. |

## Verification Checklist

- `GET /api/v1/health` -> all `ok`, `courses_indexed` ~5000+
- `GET /api/v1/admin/categories` -> 12 categories
- Create/edit/delete a role in the Admin module
- Upload a resume in the Employee module and review the dashboard

## Key Design Notes

- **No Docker, no `.devcontainer`, no authentication** (MVP).
- **Courses are script-generated only** — not admin-managed.
- **`embedding_text` is never stored** in MongoDB; it is computed on-the-fly.
- **Skill category taxonomy** (20 industry-standard categories, plus admin-defined
  **custom categories**) lives in `backend/app/constants/categories.py` and
  `frontend/src/constants/categories.js` as the single source of truth.
