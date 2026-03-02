# Digital Book Source Retrieval System

**Indexed Search Engine for Controlled Digital Library**

## Project Overview

An information retrieval system that indexes a controlled collection of books and retrieves the most relevant pages for a given text query using an **inverted index** and **BM25 ranking** — no AI/ML models used.

- 30 books across 5 domains (Academic, History, Literature, Philosophy, Science)
- ~16 000 pages indexed, ~104 000 unique terms
- BM25 scoring with proximity bonus and exact-phrase boost
- OCR fallback (Tesseract) for scanned/image-only PDF pages

## Tech Stack

- **Backend**: Python 3.10+
- **Database**: MongoDB (`book_search_system`)
- **OCR**: Tesseract OCR + pdf2image
- **PDF parsing**: PyMuPDF (fitz)
- **Algorithm**: Inverted Index + BM25 Ranking
- **Testing**: pytest (56 tests — 32 unit, 24 integration)

## Project Structure

```
backend/
  main.py                    # Interactive search CLI
  data/search_index.pkl      # Pre-built BM25 index
  src/
    config/db.py             # MongoDB connection
    models/book.py           # BookModel
    models/page.py           # PageModel
    services/
      tokenizer_service.py   # tokenize()
      search_service.py      # BM25 + proximity + enhanced_search
      index_service.py       # build_index / load_index
      ingestion_service.py   # ingest_books (OCR fallback)
    utils/logger.py          # Centralised logging
books/                       # 30 PDFs in domain sub-folders
scripts/
  ingest_books.py            # Ingest all PDFs into MongoDB
  build_index.py             # Build BM25 index from MongoDB
  export_data.py             # Export metadata to CSV
tests/
  unit/                      # 32 unit tests
  integration/               # 24 integration tests
docs/                        # Problem statement, requirements, scope
dataset/                     # Exported CSV files (generated)
```

## Setup

1. **Install dependencies**

   ```bash
   pip install pymongo pymupdf pytesseract pdf2image Pillow pytest pytest-mock
   ```

2. **Install Tesseract OCR** (Windows)

   Download from https://github.com/UB-Mannheim/tesseract/wiki  
   Default path expected: `C:\Program Files\Tesseract-OCR\tesseract.exe`

3. **Start MongoDB**

   ```bash
   mongod
   ```

4. **Ingest books** (only needed once)

   ```bash
   python scripts/ingest_books.py
   ```

5. **Build search index** (only needed once or after adding books)

   ```bash
   python scripts/build_index.py
   ```

6. **Run search**

   ```bash
   python backend/main.py
   ```

## Running Tests

```bash
pytest tests/        # all 56 tests
pytest tests/unit/   # unit tests only (no MongoDB needed for most)
pytest tests/integration/  # requires live MongoDB + index
```

## Documentation

See the `docs/` folder:

- [Problem Statement](docs/problem-statement.md)
- [Requirements](docs/requirements.md)
- [Scope](docs/scope.md)

## License

MIT
