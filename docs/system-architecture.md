# System Architecture

## Components
- Frontend: React + TypeScript (Vite)
- Backend: Flask API
- Database: MongoDB (`book_search_system`)
- Search indexes:
	- `backend/data/search_index.pkl` (BM25 positional index)
	- `backend/data/semantic.index` + `backend/data/semantic_meta.pkl` + `backend/data/semantic_page_map.pkl` (FAISS + metadata)
- File storage: `backend/books/` (PDFs)

## High-Level Flow
1. Admin uploads a book (filesystem + DB metadata)
2. Admin processes the book (extract text into `pages`)
3. Admin builds the indexes with term positions + semantic embeddings (writes BM25 + FAISS files)
4. User searches (BM25 candidate retrieval + phrase/proximity reranking + semantic reranking)
5. User opens the matched page preview (PDF page)

## Directory Structure
Expected root structure:
- `backend/`
- `frontend/`
- `docs/`

Backend structure:
- `backend/app/routes/` HTTP endpoints
- `backend/app/services/` business logic
- `backend/app/models/` schema helpers/constants
- `backend/app/utils/` shared helpers
- `backend/app/config/` settings, database, paths

Runtime folders (ignored by git):
- `backend/books/` uploaded PDFs
- `backend/data/` generated index artifacts

## Backend Layers
- Routes layer: validates inputs and returns HTTP responses
- Services layer: search, indexing, ingestion, job execution
- Models layer: document shapes, defaults, constants
- Utils layer: auth/JWT, PDF helpers, storage path normalization

## Indexing Design
- Search runs only on prebuilt indexes (fast runtime)
- Index builds from processed books/pages and stores token positions + semantic chunk embeddings
- Default behavior is incremental (avoid full rebuild when possible)
- Ranking uses BM25 as baseline, then applies order/proximity boosts and semantic reranking

## PDF Preview Design
- Extracted text is used for ranking/snippets only
- Preview uses PDF content for the final user-facing view

Endpoints:
- `GET /api/page/<page_id>/pdf` returns a single-page PDF for safe viewing
- `GET /api/book/<book_id>/download` returns the full PDF (login required)

## Maintenance Scripts
These scripts are intended for developers (local setup/maintenance). They are not called by the HTTP API routes.

- `backend/scripts/init_db_schema.py`: ensures MongoDB collections and indexes exist.
- `backend/scripts/migrate_backfill.py`: backfills missing/default fields in existing `books` and `pages` documents.
