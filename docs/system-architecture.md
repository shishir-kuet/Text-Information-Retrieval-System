# System Architecture

## Components
- TIRS frontend: React + TypeScript (Vite)
- TIRS backend: Flask API
- Library frontend: React + TypeScript (Vite)
- Library backend: Flask API
- MongoDB databases:
	- `book_search_system` for TIRS users/search logs
	- `library_system` for library books/pages/page_chunks
- Search indexes:
	- `backend/data/search_index.pkl` (BM25 positional index)
	- `backend/data/semantic.index` + `backend/data/semantic_meta.pkl` + `backend/data/semantic_page_map.pkl` (FAISS + metadata)
- File storage:
	- `backend-library/books/` for uploaded PDFs
	- `backend/data/` for TIRS local index artifacts

## High-Level Flow
1. Admin uploads a book in the Library subsystem.
2. Library backend saves the PDF and extracts page text into the Library database.
3. TIRS admin syncs the latest book metadata from the Library API.
4. TIRS builds/updates local search indexes from Library page text and stores only local index artifacts.
5. User searches against local indexes only.
6. User opens a page preview; TIRS may fetch page details or PDF bytes from the Library API.

## Directory Structure
Expected root structure:
- `backend/`
- `frontend/`
- `backend-library/`
- `frontend-library/`
- `docs/`

Backend structure:
- `backend/app/routes/` TIRS HTTP endpoints
- `backend/app/services/` TIRS business logic
- `backend/app/models/` schema helpers/constants
- `backend/app/utils/` shared helpers
- `backend/app/config/` settings, database, paths

Library backend structure:
- `backend-library/app/routes/` Library HTTP endpoints
- `backend-library/app/services/` Library ingestion and page retrieval logic
- `backend-library/app/models/` Library document helpers
- `backend-library/app/utils/` Library helpers
- `backend-library/app/config/` settings, database, paths

Runtime folders (ignored by git):
- `backend-library/books/` uploaded PDFs
- `backend/data/` generated index artifacts

## Backend Layers
- TIRS routes layer: search, auth, history, admin sync/index, library proxy
- TIRS services layer: search, semantic reranking, index loading, search logging
- Library routes layer: upload, processing, page retrieval, PDF download
- Library services layer: PDF ingestion, page extraction, library storage
- Models layer: document shapes, defaults, constants
- Utils layer: auth/JWT, PDF helpers, storage path normalization

## Summarization Design
Summary endpoint:
- `POST /api/page/<page_id>/summary`

Implementation:
- Route layer (`public.py`) resolves page text and calls `AiSummaryService`.
- Service layer (`ai_summary_service.py`) supports provider selection by env:
	- `SUMMARY_PROVIDER=gemini`
	- `SUMMARY_PROVIDER=huggingface`
	- `SUMMARY_PROVIDER=auto`
- Hugging Face requests are attempted with compatible endpoint candidates for better runtime portability.

Failure handling:
- If remote inference fails, service returns deterministic local extractive summary.
- This keeps the summarize button operational and avoids user-facing hard failures on provider outages/quota limits.

## Indexing Design
- Search runs only on prebuilt local indexes in TIRS
- TIRS fetches Library page text during sync/indexing, not during every search query
- The BM25 index stores term positions and page text metadata locally
- The semantic index stores FAISS vectors and chunk metadata locally
- Ranking uses BM25 as baseline, then applies order/proximity boosts and semantic reranking

## PDF Preview Design
- Extracted text is used for ranking/snippets only
- Preview uses the Library PDF/page stream for the final user-facing view

Endpoints:
- `GET /api/page/<page_id>/pdf` returns a single-page PDF for safe viewing
- `GET /api/book/<book_id>/download` returns the full PDF (login required)

## Maintenance Scripts
These scripts are intended for developers (local setup/maintenance). They are not called by the HTTP API routes.

- `backend/scripts/init_db_schema.py`: ensures TIRS MongoDB collections and indexes exist.
- `backend/scripts/migrate_backfill.py`: legacy helper for older TIRS documents.

## Split Responsibilities

### Library subsystem
- Upload PDFs
- Store PDF files
- Extract page text with OCR fallback
- Serve book/page metadata and PDF/page preview content

### TIRS subsystem
- Authenticate users
- Record search history and search logs
- Sync books from the Library subsystem
- Build local BM25 and semantic indexes
- Execute fast search from local artifacts only
