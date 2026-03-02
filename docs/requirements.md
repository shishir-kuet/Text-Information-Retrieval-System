# System Requirements

## Functional Requirements (FR)

### Search Functionality

**FR-1: Text-Based Search**

- User submits a sentence or paragraph as a query via the CLI
- System tokenises and normalises the query (lowercase, remove punctuation)
- Minimum 1 valid token required

**FR-2: Search Results**

- System returns the top-10 best-matching pages
- Each result includes:
  - Book title and domain (subject area)
  - Page number
  - BM25 relevance score (with proximity and exact-phrase bonuses)
  - Text preview (first 300 characters of the page)

**FR-3: Page Preview**

- Each result displays a text snippet from the matched page
- Shows book metadata (title, domain) and page number alongside the snippet

### Book Ingestion

**FR-4: Book Ingestion Script**

- `scripts/ingest_books.py` scans `books/<domain>/` sub-folders for PDF files
- Each PDF is processed page-by-page and stored in MongoDB
- Text-based PDFs use PyMuPDF (fitz) for fast extraction
- Only PDF format processed; other file types ignored

**FR-5: OCR Text Extraction**

- Pages with fewer than 50 characters from normal extraction trigger OCR fallback
- Tesseract OCR converts the page image (200 DPI) to text
- OCR errors are logged and handled gracefully (page stored with empty text)
- Supports incremental ingestion: existing books are not duplicated

**FR-6: Index Build**

- `scripts/build_index.py` reads all pages from MongoDB and builds the inverted index
- Index includes:
  - Inverted index: `term → {page_id: term_frequency}`
  - Term frequencies per document
  - Document lengths (token counts)
  - Books metadata map (`page_id → {title, page_number, domain}`)
- Index is saved to `backend/data/search_index.pkl`
- Build time and total unique terms are reported

**FR-7: Data Export**

- `scripts/export_data.py` exports book and page metadata to CSV files in `dataset/`
- Page text content is excluded from the export (metadata only)

### System Logging

**FR-8: Operational Logging**

- All services use the centralised `utils/logger.py` logger
- INFO-level logs for normal operations (ingestion progress, index build, search)
- WARNING/ERROR logs for OCR failures, missing files, and unexpected exceptions

---

## Non-Functional Requirements (NFR)

### Performance

**NFR-1: Search Response Time**

- Search queries must return results within 2 seconds on the full 30-book / ~16 000-page collection
- BM25 candidate set is limited to top-200 before the MongoDB batch fetch to bound latency
- Performance must be measured and reported (latency vs. dataset size)

**NFR-2: Index Build Time**

- Index building must complete in a reasonable time for medium-sized collections
- Progress must be logged every 1 000 pages
- Build time and total unique terms must be reported on completion

**NFR-3: Memory & Storage Efficiency**

- Index file size should be monitored and kept reasonable
- Inverted index uses `{page_id: tf}` dicts (compact representation)
- Index stored as a single `.pkl` file under `backend/data/`

### Reliability

**NFR-4: Error Handling**

- Invalid or unreadable PDFs handled gracefully (logged, ingestion continues)
- Empty queries rejected before search executes
- OCR failures logged without stopping the ingestion pipeline

**NFR-5: Data Integrity**

- Incremental ingestion prevents duplicate books (checks existing `book_id`)
- Each page has a unique `page_id` (`<book_id>_<page_number>`)
- `page_id` field is indexed in MongoDB for fast batch lookups

### Maintainability

**NFR-6: Code Quality**

- Layered Python architecture: `config/`, `models/`, `services/`, `utils/`
- Each service has a single responsibility (tokenizer, search, index, ingestion)
- No hardcoded credentials; MongoDB URI is defined in `config/db.py`
- Consistent naming conventions following PEP 8

**NFR-7: Documentation**

- Algorithms (BM25, proximity scoring) documented with inline comments
- System requirements, scope, and problem statement maintained in `docs/`
- README covers setup and usage instructions

**NFR-8: Version Control**

- Professional Git workflow (branches, meaningful commits)
- No secrets or large binaries committed to the repository

### Testability

**NFR-9: Unit Testing**

- Core modules (tokenizer, BM25 scorer, proximity scorer, index loader) have dedicated unit tests
- Tests use mocks for MongoDB to run without a live database
- Minimum 30 unit test cases covering normal and edge cases

**NFR-10: Integration Testing**

- Integration tests connect to the real MongoDB instance (read-only)
- Tests verify: DB connectivity, document counts, document structure, batch fetch, full search pipeline
- Minimum 20 integration test cases

### Deployment

**NFR-11: Environment Configuration**

- MongoDB URI and DB name configurable in `backend/src/config/db.py`
- Index path configurable via `Path` constants in each service
- No secrets committed to the repository

**NFR-12: Cross-Platform**

- Python 3.10+ compatible
- Works on Windows, Linux, macOS
- Tesseract path configurable in `ingestion_service.py`

---

## Constraints

1. Must use Python for backend
2. Must use MongoDB for database
3. Must NOT use AI/ML libraries for core search functionality (BM25 algorithm only)
4. Must include unit and integration tests (pytest)
5. Must demonstrate a professional, layered codebase structure
6. Must complete within the project timeframe
