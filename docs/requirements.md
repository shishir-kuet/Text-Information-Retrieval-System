# Project Requirements

## Project
- Name: Text Information Retrieval System
- Type: Academic system project

## Goal
Given a line, sentence, or paragraph of text, the system identifies:
- Which book the text belongs to
- Which page contains the text
- A relevant snippet
- A preview of the original PDF page

## Non-Goals
- Do not replace BM25; keep it as the primary candidate retriever.

## Core Techniques
- Inverted index
- BM25 ranking
- Positional indexing for phrase/proximity scoring
- Semantic embeddings (MiniLM) for reranking
- FAISS for vector similarity search
- OCR (Tesseract) for scanned PDFs when needed

## Key Principle
Extracted page text is used for:
- Indexing
- Ranking
- Snippet generation

But the user-facing preview must show the original page content from the PDF (not the extracted text), because extraction can be noisy.

## Architecture Rules
Project root structure:
- `backend/` contains backend code and backend runtime folders
- `frontend/` contains frontend code (placeholder for now)
- `docs/` contains documentation

Frontend and backend remain separated.

## File Storage Rules
- Uploaded book PDFs are stored on the server filesystem under `backend/books/`.
- The search index is stored under `backend/data/search_index.pkl`.
- These runtime artifacts must not be committed to Git.

## Database Strategy
The MongoDB database already contains existing `books` and `pages` data for the controlled dataset.

Strategy: compatible schema evolution
- Preserve existing data
- Extend documents with missing fields
- Avoid destructive renames or wipes

Final collections:
- `books`
- `pages`
- `page_chunks`
- `users`
- `search_logs`

## Book Workflow
The ingestion pipeline is intentionally separated:

1. Upload
- API: `POST /api/admin/upload`
- Saves PDF to filesystem
- Creates a `books` document
- Sets `status=uploaded`

2. Process
- API: `POST /api/admin/process-books`
- Extracts text (OCR or direct extraction)
- Inserts/updates `pages` for uploaded books
- Sets `status=processed`

3. Build Index
- API: `POST /api/admin/index/build`
- Builds/updates the positional inverted index from processed books
- Builds/updates the semantic chunk index
- Writes `backend/data/search_index.pkl` + semantic index artifacts
- Marks processed books as `indexed`

## Search Workflow
- API: `POST /api/search`
- Uses the prebuilt index for candidate retrieval and BM25 ranking
- Applies phrase/proximity reranking so exact-order and near-order matches are prioritized
- Applies semantic reranking using FAISS + MiniLM embeddings
- Returns `book_id`, `title`, `page_id`, `page_number`, `score`, `snippet`

## Page Preview Workflow
APIs:
- `GET /api/page/<page_id>` returns stored page metadata and extracted text
- `GET /api/page/<page_id>/pdf` returns a single-page PDF for that page_id

Note: The single-page PDF endpoint is used to avoid exposing the full book PDF to guests via the browser PDF viewer.

## AI Summary Workflow
API:
- `POST /api/page/<page_id>/summary`

Behavior:
- Supports provider-based summarization via environment config.
- `SUMMARY_PROVIDER=gemini` uses Gemini.
- `SUMMARY_PROVIDER=huggingface` uses Hugging Face Inference.
- `SUMMARY_PROVIDER=auto` tries configured providers in sequence.

Reliability requirement:
- If external provider calls fail (quota/rate-limit, invalid endpoint, or network), the API must return a local extractive summary instead of failing the user action.
- Response includes `provider` value so UI can indicate which summarizer produced the output (`gemini`, `huggingface`, or `extractive`).

## Authentication and Access Rules
JWT is used for authentication.

Guest users can:
- Search
- Preview matched pages

Logged-in users can:
- Search
- Preview pages
- Download full books
- View and manage their own history

Admins can:
- Upload books
- Process books
- Build index
- View books list, index stats, and search logs

Protected endpoints require `Authorization: Bearer <token>`.

Logout:
- API: `POST /api/auth/logout`
- Note: JWT is stateless; logout is implemented by deleting the token on the client.

## Git Rules
Do not commit:
- `backend/books/`
- `backend/data/search_index.pkl`
- `.env`
- `.venv/`, `venv/`
- `__pycache__/`, `*.pyc`
- `frontend/node_modules/`, `frontend/dist/`

Commit only source code, configuration templates, and documentation.



