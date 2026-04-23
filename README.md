# Text Information Retrieval System (TIRS)

This repository now contains two local subsystems:
- TIRS: auth, search, history, local indexing, search logs
- Library: upload, processing, page extraction, library-side book/page storage

Both subsystems run locally and use local MongoDB instances/databases.

## Features
- BM25 search over a persisted inverted index
- Phrase/proximity-aware reranking
- Hybrid reranking with MiniLM embeddings + FAISS semantic index
- Library-side PDF upload and extraction with OCR fallback when needed
- Page-level preview using the original PDF page
- Auth + admin workflow for TIRS retrieval-side sync/index tasks
- Search history for logged-in users

## Tech Stack
- TIRS backend: Python + Flask
- Library backend: Python + Flask
- Database: local MongoDB
- Search/Index: positional inverted index + BM25 + phrase/proximity reranking (pickle), plus FAISS semantic index
- PDF/Text extraction: PyMuPDF + optional OCR (Tesseract + pdf2image)
- Frontends: React + TypeScript (Vite)

## Repo Structure
- `backend/` TIRS Flask API and services
- `frontend/` TIRS React UI
- `backend-library/` Library Flask API
- `frontend-library/` Library React UI
- `docs/` System docs (architecture, schema, requirements)

## Local Setup

Prereqs:
- Python 3.10+
- Node.js 18+
- Local MongoDB running
- Optional OCR: Tesseract and Poppler for `pdf2image`

Start the Library subsystem:
```bash
cd backend-library
python run.py
```

Start the TIRS subsystem:
```bash
cd backend
python run.py
```

Start the TIRS frontend:
```bash
cd frontend
npm install
npm run dev
```

Start the Library frontend:
```bash
cd frontend-library
npm install
npm run dev
```

## Environment Variables
Create `.env` at the project root or in the subsystem folders.

TIRS backend:
- `MONGO_URI` (default `mongodb://localhost:27017/`)
- `DB_NAME` (default `book_search_system`)
- `LIBRARY_API_BASE_URL` (default `http://127.0.0.1:5100`)
- `JWT_SECRET`
- `BOOKS_PATH`, `INDEX_PATH`, `SEMANTIC_INDEX_PATH`, `SEMANTIC_META_PATH`, `SEMANTIC_PAGE_MAP_PATH`
- `SEMANTIC_MODEL_NAME`
- `CHUNK_MIN_WORDS`, `CHUNK_MAX_WORDS`, `CHUNK_TARGET_WORDS`
- `SEMANTIC_TOP_K`
- `SERVER_HOST`, `SERVER_PORT`, `SERVER_DEBUG`

Library backend:
- `MONGO_URI`
- `LIBRARY_DB_NAME` (default `library_system`)
- `LIBRARY_SERVER_HOST`, `LIBRARY_SERVER_PORT`, `LIBRARY_SERVER_DEBUG`
- `LIBRARY_BOOKS_PATH`, `LIBRARY_DATA_PATH`
- `TESSERACT_PATH`
- `JWT_SECRET` (shared only if you want consistent secrets; not required for library APIs)

AI summarization (TIRS, optional):
- Provider selector: `SUMMARY_PROVIDER=auto|gemini|huggingface`
- Gemini:
	- `GEMINI_API_KEY`
	- Optional: `GEMINI_API_BASE`, `GEMINI_MODEL`
	- Required template: `GEMINI_SUMMARY_PROMPT_TEMPLATE`
	- Tip: use `\\n` inside `.env` values for multi-line prompts
- Hugging Face:
	- `HF_API_KEY`
	- Optional: `HF_API_BASE` (recommended: `https://router.huggingface.co/hf-inference/models`)
	- `HF_MODEL` (example: `facebook/bart-large-cnn`)
- Reliability behavior:
	- If remote AI providers fail (quota, endpoint, network), backend falls back to local extractive summary.
	- The API still returns success with `provider: "extractive"` so the summarize button remains usable.

Frontend env vars:
- TIRS frontend: `VITE_API_BASE_URL` (default `http://127.0.0.1:5000`)
- Library frontend: `VITE_LIBRARY_API_BASE_URL` (default `http://127.0.0.1:5100`)

## Admin Workflow (Typical)
1. Upload books in the Library subsystem
2. Process uploaded books in the Library subsystem
3. Sync books into TIRS
4. Build/update the TIRS local search index

## Maintenance Scripts
These scripts are for local setup/maintenance and are not called by the API.
- `python backend/scripts/init_db_schema.py`
- `python backend/scripts/migrate_backfill.py`

## API Overview (Selected)
Public:
- `GET /api/health`
- `POST /api/search`
- `GET /api/page/<page_id>`
- `POST /api/page/<page_id>/summary` (AI summary; supports Gemini/Hugging Face + local extractive fallback)
- `GET /api/page/<page_id>/pdf` (single-page PDF)
- `GET /api/library/books`, `GET /api/library/books/<book_id>`, `GET /api/library/books/<book_id>/pages`, `GET /api/library/pages/<page_id>`, `GET /api/library/pages/<page_id>/text`

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
- `POST /api/admin/sync/books`
- `POST /api/admin/index/build`
- `GET /api/admin/index/stats`
- `GET /api/admin/books`
- `GET /api/admin/logs/search`

## Git Hygiene
This repo ignores runtime/generated files like:
- Uploaded PDFs (`backend-library/books/`)
- Built search index artifacts (`backend/data/*.pkl`)
- Virtual envs, node_modules, build outputs

## Documentation
See `docs/` for:
- `database-schema.md`
- `system-architecture.md`
- `requirements.md`