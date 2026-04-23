# Text Information Retrieval System (TIRS)

A full-stack academic project for classical information retrieval. Given a line, sentence, or paragraph, the system searches a prebuilt inverted index (BM25-style ranking) and returns the most relevant book + page matches with a PDF page preview.

## Features
- BM25 search over a persisted inverted index
- Phrase/proximity-aware reranking (exact order and near-order matches score higher)
- Hybrid reranking with MiniLM embeddings + FAISS vector index
- PDF ingestion with text extraction (OCR fallback when needed)
- Page-level preview using the original PDF page
- Auth + admin workflow (upload, process, index)
- Search history for logged-in users

## Tech Stack
- Backend: Python + Flask
- Database: MongoDB
- Search/Index: Positional inverted index + BM25 + phrase/proximity reranking (pickle), plus FAISS semantic index
- PDF/Text extraction: PyMuPDF + optional OCR (Tesseract + pdf2image)
- Frontend: React + TypeScript (Vite)

## Repo Structure
- `backend/` Flask API and services
- `frontend/` React UI
- `docs/` System docs (architecture, schema, requirements)

## Docker Quickstart (Recommended)

Prereqs:
- Docker Desktop (Compose enabled)

Start everything:
```bash
docker compose up --build -d
```

Endpoints:
- Frontend: `http://127.0.0.1:5173`
- Backend API: `http://127.0.0.1:5000`
- Health check: `GET http://127.0.0.1:5000/api/health`

Stop:
```bash
docker compose down
```

## Local Setup (Optional)

### Backend
Prereqs:
- Python 3.10+
- MongoDB running locally
- Optional OCR: Tesseract (and Poppler for `pdf2image` on Windows)

Install deps:
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

Run API:
```bash
cd backend
python run.py
```

### Frontend
Prereqs:
- Node.js 18+ recommended

Install + run:
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables
Create a `.env` file at the project root or in `backend/.env` (do not commit it). Use `backend/.env.example` as a starting point.

Common backend vars:
- `MONGO_URI` (default `mongodb://localhost:27017/`)
- `DB_NAME` (default `book_search_system`)
- `JWT_SECRET` (set a strong secret)
- `BOOKS_PATH` (default `backend/books`)
- `INDEX_PATH` (default `backend/data/search_index.pkl`)
- `SEMANTIC_INDEX_PATH` (default `backend/data/semantic.index`)
- `SEMANTIC_META_PATH` (default `backend/data/semantic_meta.pkl`)
- `SEMANTIC_PAGE_MAP_PATH` (default `backend/data/semantic_page_map.pkl`)
- `SEMANTIC_MODEL_NAME` (default `sentence-transformers/all-MiniLM-L6-v2`)
- `CHUNK_MIN_WORDS` (default `200`)
- `CHUNK_MAX_WORDS` (default `300`)
- `CHUNK_TARGET_WORDS` (default `250`)
- `SEMANTIC_TOP_K` (default `200`)
- `SERVER_HOST` (default `0.0.0.0`)
- `SERVER_PORT` (default `5000`)
- `SERVER_DEBUG` (default `true`)
- `TESSERACT_PATH` (Windows example in `.env.example`)
- `PROCESS_CLEAR_EXISTING_DATA` (default `false`)

AI summarization (optional):
- Gemini: set `GEMINI_API_KEY` (optional `GEMINI_API_BASE`, `GEMINI_MODEL`)
	- Prompt template (required): `GEMINI_SUMMARY_PROMPT_TEMPLATE`
	- Tip: use `\\n` inside `.env` values for multi-line prompts

Frontend env vars (optional):
- `VITE_API_BASE_URL` (default `http://127.0.0.1:5000`)

## Admin Workflow (Typical)
1. Upload books (PDF)
2. Process uploaded books (extract pages)
3. Build index (BM25 index + semantic chunk embeddings + FAISS)

## Maintenance Scripts
These scripts are for local setup/maintenance and are not called by the API.
- `python backend/scripts/init_db_schema.py`
- `python backend/scripts/migrate_backfill.py`

## API Overview (Selected)
Public:
- `GET /api/health`
- `POST /api/search`
- `GET /api/page/<page_id>`
- `POST /api/page/<page_id>/summary` (AI summary; requires Gemini env vars)
- `GET /api/page/<page_id>/pdf` (single-page PDF)

Auth:
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`

User:
- `GET /api/history`
- `DELETE /api/history/<log_id>`
- `DELETE /api/history`
- `GET /api/book/<book_id>/download` (login required)

Admin:
- `POST /api/admin/upload`
- `POST /api/admin/index/build`
- `GET /api/admin/index/stats`
- `GET /api/admin/books`
- `GET /api/admin/logs/search`

## Git Hygiene
This repo ignores runtime/generated files like:
- Uploaded PDFs (`backend/books/`)
- Built search index artifacts (`backend/data/*.pkl`)
- Virtual envs, node_modules, build outputs

## Documentation
See `docs/` for:
- `database-schema.md`
- `system-architecture.md`
- `requirements.md`