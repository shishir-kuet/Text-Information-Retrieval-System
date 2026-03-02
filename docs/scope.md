# System Scope

## In Scope

The system operates on a controlled digital library (30 books, 5 domains). It supports ingestion of PDF books, BM25-based search over indexed pages, and data export — all via a Python backend.

### Features Included

1. **Book Ingestion (`scripts/ingest_books.py`)**
   - Scans `books/<domain>/` sub-folders for PDF files
   - Extracts text page-by-page using PyMuPDF
   - Falls back to Tesseract OCR for image-only pages
   - Stores book metadata and page text in MongoDB
   - Supports incremental runs (will not duplicate already-ingested books)

2. **Text Extraction (OCR)**
   - Page-by-page text extraction using PyMuPDF (fitz)
   - OCR fallback via Tesseract for pages with fewer than 50 characters
   - PDF pages rasterised at 200 DPI before OCR
   - Error handling: OCR failures are logged; ingestion continues

3. **Indexing System (`scripts/build_index.py`)**
   - Builds inverted index from all pages in MongoDB
   - Tokenisation: lowercase + alphanumeric-only filter
   - Posting lists: `term → {page_id: term_frequency}` (dict of dicts)
   - Stores document lengths and books metadata map
   - Serialised to `backend/data/search_index.pkl`

4. **Search & Ranking (`backend/main.py`)**
   - Tokenises and normalises query
   - BM25 scoring (k1=1.5, b=0.75) over inverted index
   - Top-200 BM25 candidates → single batch MongoDB fetch
   - Proximity bonus (+50/+30/+10) for terms appearing close together
   - Exact-phrase bonus (+100) for verbatim match in page text
   - Returns top-10 results with title, domain, page number, score, and preview

5. **Data Export (`scripts/export_data.py`)**
   - Exports book metadata and page metadata (no text) to CSV
   - Output written to `dataset/books.csv` and `dataset/pages.csv`

6. **Testing**
   - 32 unit tests covering tokenizer, BM25 scorer, proximity scorer, exact-phrase check, enhanced search, and index loader
   - 24 integration tests covering DB connectivity, document counts, document structure, and full search pipeline
   - Run with `pytest tests/`

## Out of Scope

1. Web or REST API frontend (no HTTP server implemented)
2. User authentication, registration, or role management
3. Search history or per-user features
4. Searching external web pages or public internet
5. Copyright-violating public distribution of book PDFs
6. Real-time collaborative features
7. Mobile application development
8. Advanced NLP (summarisation, translation, semantic search)
9. Handwritten text recognition (only printed OCR text)

## Assumptions

1. PDF files are organised under `books/<domain>/` sub-folders (e.g. `books/History/`)
2. Books contain printed text (not handwritten)
3. Admin has permission to store and process book texts for academic purposes
4. Dataset is in English
5. Books have reasonable scan quality for OCR
6. MongoDB is running on `localhost:27017`
7. Tesseract OCR is installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`
8. Python 3.10+ is available in the environment

## Limitations

1. **OCR Accuracy**: Errors may occur for poor-quality scans, unusual fonts, or low-resolution images
2. **OCR Processing Time**: OCR is significantly slower than native PDF text extraction
3. **Lexical Matching Only**: BM25 matches exact tokens; paraphrased or semantically equivalent queries may score lower
4. **Batch Index Rebuild**: Index must be fully rebuilt after adding new books (no incremental update)
5. **Language**: English only
6. **Scale**: Optimised for small-to-medium collections (up to ~1 000 books / ~100 000 pages)
7. **Special Characters**: Tables, mathematical symbols, and complex layouts may not OCR accurately

## Future Enhancements (Out of Current Scope)

- REST API layer (Flask/FastAPI) for web or mobile access
- Incremental index updates without full rebuild
- Multi-language support
- Semantic / embedding-based search
- Book recommendation system
- Web-based search UI
- Advanced analytics dashboard
- Export of highlighted page PDFs
