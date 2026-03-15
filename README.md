# Text Information Retrieval System

A Flask + MongoDB academic project that performs classical information retrieval over a controlled digital library.

Given a line/sentence/paragraph, the system returns the most relevant book + page matches using an inverted index and BM25 ranking, and lets the user preview the original PDF page.

## Tech Stack
- Backend: Python, Flask
- Database: MongoDB
- Search: inverted index + BM25 (index persisted as pickle)
- OCR/Text extraction: PyMuPDF + Tesseract (when needed)
- Frontend: React + TypeScript (Vite) planned (not included in this branch yet)

## Repository Structure
- `backend/` Flask backend
- `frontend/` placeholder (kept empty for now)
- `docs/` documentation

## Key Runtime Files (Not Committed)
- `backend/books/` uploaded PDFs
- `backend/data/search_index.pkl` generated search index
- `.env` secrets

## Setup (Backend)
Prerequisites:
- Python 3.10+ (3.12 recommended)
- MongoDB running locally
- Tesseract installed (Windows default path is configurable)

Create venv and install deps:
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

Run the backend:
```bash
cd backend
python run.py
```

Health check:
- `GET http://127.0.0.1:5000/api/health`

## Environment Variables
Create `.env` (not committed) at project root or `backend/.env`.

Common vars:
- `MONGO_URI` (default `mongodb://localhost:27017/`)
- `DB_NAME` (default `book_search_system`)
- `JWT_SECRET` (set a strong secret)
- `SERVER_HOST` (default `0.0.0.0`)
- `SERVER_PORT` (default `5000`)
- `SERVER_DEBUG` (default `true`)
- `TESSERACT_PATH` (Windows path to tesseract.exe)
## Database Scripts
These scripts are helpers for local setup and safe, compatible data backfill. They are not called by the API at runtime.

- Initialize collections + indexes:
  - `python backend/scripts/init_db_schema.py`
- Backfill missing/default fields for existing data (compatible migration):
  - `python backend/scripts/migrate_backfill.py`

Tip: set `MONGO_URI` and `DB_NAME` in `.env` first if you use a non-default database.

## API Summary
Public:
- `GET /api/health`
- `GET /api/stats`
- `POST /api/search`
- `GET /api/page/<page_id>`
- `GET /api/page/<page_id>/pdf-preview`
- `GET /api/page/<page_id>/pdf` (single-page PDF)

Auth:
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout` (client clears token)

User:
- `GET /api/history`
- `DELETE /api/history/<log_id>`
- `DELETE /api/history`
- `GET /api/book/<book_id>/download` (login required)

Admin (admin JWT required):
- `POST /api/admin/upload`
- `POST /api/admin/process-book/<book_id>`
- `POST /api/admin/index/build`
- `GET /api/admin/index/stats`
- `GET /api/admin/books`
- `GET /api/admin/logs/search`
- `GET /api/admin/jobs`
- `GET /api/admin/jobs/<job_id>`

## Notes
- The database already contains an existing dataset of books/pages; do not wipe production/demo data.
- Upload, process, and index are separated to keep user search fast.




