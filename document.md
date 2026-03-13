# Digital Book Retrieval System - Project Document

Date: 2026-03-13

## 1) Project Overview

এই project-এর প্রধান লক্ষ্য হলো একটি controlled digital library থেকে user-এর text query অনুযায়ী relevant book page খুঁজে বের করা।

- Backend-এ BM25-based lexical search ব্যবহার করা হয়েছে।
- Database হিসেবে MongoDB ব্যবহার করা হয়েছে।
- PDF ingestion pipeline page-wise text extract করে search index build করে।
- Frontend (React + Vite) থেকে user query submit, ranked results দেখা এবং full page reading করা যায়।

সংক্ষেপে, এটি একটি searchable book retrieval system যেখানে query -> ranking -> result page flow end-to-end কাজ করে।

## 2) High-level architecture

System টি মূলত 4টি layer-এ কাজ করে:

1. Data Ingestion Layer

- books folder domain-wise scan করে PDF file detect করে।
- PyMuPDF দিয়ে embedded text extraction করা হয়।
- যেখানে text কম, সেখানে OCR fallback (Tesseract) ব্যবহার হয়।
- MongoDB-র books এবং pages collection-এ data save হয়।

2. Indexing Layer

- MongoDB pages থেকে tokenization করে inverted index build করা হয়।
- BM25 সম্পর্কিত structures (doc length, posting list, metadata map) serialize করে backend/data/search_index.pkl-এ রাখা হয়।

3. Search Layer

- Query tokenize করা হয়।
- BM25 score calculate করা হয়।
- Top candidates fetch করে proximity bonus + exact phrase bonus যোগ করা হয়।
- Final top results API/CLI-তে return করা হয়।

4. Presentation Layer

- Flask API endpoints দিয়ে data serve করা হয়।
- React UI-তে search input, result cards, page view, এবং previous/next page navigation দেওয়া হয়েছে।

## 3) Major components and what they do

### Backend

- backend/app.py
  Flask REST API:
  - GET /api/health
  - GET /api/stats
  - POST /api/search
  - GET /api/page/<page_id>

- backend/main.py
  CLI-based interactive search interface।

- backend/src/services/ingestion_service.py
  PDF text extraction, OCR fallback, display page number detection, MongoDB insertion।

- backend/src/services/index_service.py
  Inverted index build + load logic।

- backend/src/services/search_service.py
  BM25 scoring + proximity + exact phrase boost + result formatting।

- backend/src/services/tokenizer_service.py
  Basic normalization/tokenization।

- backend/src/config/db.py
  MongoDB connection config (বর্তমানে hardcoded localhost URI)।

- backend/src/models/book.py, backend/src/models/page.py
  MongoDB collection-এর জন্য data access wrappers।

### Scripts

- scripts/ingest_books.py: run ingestion.
- scripts/build_index.py: build search index.
- scripts/export_data.py: export metadata CSV.

### Frontend

- frontend/src/pages/Home.tsx
  Landing page + query input + top-k selection।

- frontend/src/pages/Results.tsx
  /api/search call করে ranked result cards দেখায়।

- frontend/src/pages/PageView.tsx
  /api/page/<id> call করে full page text দেখায় + prev/next navigation।

- frontend/vite.config.ts
  /api proxy to localhost:5000।

### Tests

- Python tests: tests/unit + tests/integration
- Frontend tests: frontend/src/test/unit + frontend/src/test/integration

## 4) End-to-end workflow

1. Admin books folder-এ domain-wise source PDF রাখে।
2. Ingestion script run করে books/pages MongoDB-তে save করে।
3. Index build script run করে searchable index generate হয়।
4. User frontend বা CLI দিয়ে query দেয়।
5. Search service BM25 + bonus rules দিয়ে rank করে result return করে।
6. User result থেকে specific page open করে full content পড়তে পারে।

## 5) Data model summary

Books collection (example fields):

- book_id
- title
- domain
- file_path
- num_pages
- file_size_mb
- date_added

Pages collection (example fields):

- page_id
- book_id
- page_number
- display_page_number
- text_content
- word_count
- char_count

## 6) Current strengths

- Backend এবং frontend দুইটি flow present (CLI + API + UI)।
- BM25 + proximity + exact phrase combined ranking implement করা হয়েছে।
- Low-text pages-এর জন্য OCR fallback available।
- API stats এবং health endpoint আছে।
- Search result-এ metadata + preview + page navigation আছে।
- Python ও frontend উভয় দিকেই unit + integration test structure আছে।

## 7) Current problems found in project

নিচের list টি current codebase review থেকে:

1. Documentation mismatch

- README/docs-এ mostly CLI-focused architecture উল্লেখ আছে, কিন্তু codebase-এ full React frontend + Flask API active।
- README-র কিছু metric এবং setup detail code reality-এর সাথে partially outdated।

2. Frontend route inconsistency

- Home page থেকে /login এবং /register-এ navigate করে, কিন্তু router-এ এই route define করা নেই।
- ফলাফল: button click করলে dead navigation/blank route risk থাকে।

3. Stray/unexpected files in frontend root

- Empty file names যেমন "{" এবং "expect(1+1).toBe(2))" present।
- এগুলো accidental artifact হতে পারে, যা maintenance noise তৈরি করে।

4. Potential XSS risk in frontend rendering

- Results এবং PageView dangerouslySetInnerHTML ব্যবহার করে highlighted text render করে।
- Backend text untrusted হলে sanitize না থাকলে script injection risk থাকতে পারে।

5. Hardcoded environment/config values

- Mongo URI hardcoded ([backend/src/config/db.py](backend/src/config/db.py))।
- Flask app debug mode on (app.run(debug=True))।
- OCR path hardcoded Windows default path।
- Production readiness-এর জন্য env-based configuration বেশি উপযোগী।

6. Data ingestion format gap

- Ingestion service শুধু PDF (\*.pdf) scan করে।
- Workspace-এ EPUB file আছে, কিন্তু current logic-এ ingest হবে না।

7. Repository hygiene issue

- frontend/node_modules, frontend/dist, এবং \*.tsbuildinfo committed আছে।
- এতে repo heavy হয়, merge conflict chance বাড়ে, CI performance কমে।

8. Styling toolchain warning in editor diagnostics

- [frontend/src/index.css](frontend/src/index.css)-এ @theme at-rule নিয়ে diagnostic warning দেখা যাচ্ছে।
- Build fail নাও করতে পারে, তবে tooling alignment check করা দরকার।

9. Integration tests tightly coupled to specific dataset size

- Python integration tests fixed threshold ব্যবহার করে (>=30 books, >=16000 pages, >=50000 terms)।
- Dataset change হলে false failure হতে পারে।

10. Dependency management incompleteness

- Python requirements lock/setup file স্পষ্টভাবে নেই (requirements.txt/pyproject absent)।
- Reproducible environment setup কঠিন হতে পারে।

## 8) Suggested priority fixes

Priority 1 (high):

- Sanitize HTML rendering before dangerouslySetInnerHTML usage.
- debug=False and env-based config implement.
- Remove accidental files and add proper .gitignore hygiene.

Priority 2 (medium):

- README/docs update kore actual API + frontend flow include.
- /login and /register route either implement or button behavior adjust.
- Integration tests ke less dataset-dependent kora.

Priority 3 (nice to have):

- EPUB support add (optional ingestion extension).
- Python dependency file add and setup simplify.
- CSS tooling warning cleanup.

## 9) Quick run guide (current structure অনুযায়ী)

Backend:

1. MongoDB run করুন।
2. books data ingest করুন: python scripts/ingest_books.py
3. index build করুন: python scripts/build_index.py
4. API run করুন: python backend/app.py

Frontend:

1. frontend folder-এ npm install
2. npm run dev
3. Browser-এ app open করুন (default Vite port 5173)

## 10) Final assessment

Project টি functional core retrieval system হিসেবে solid।
Main algorithmic pipeline (ingestion -> indexing -> BM25 search -> page retrieval) ভালোভাবে structured।
তবে production-grade stability এবং maintainability-এর জন্য config hardcoding, security rendering risk, repo hygiene, এবং documentation mismatch-এর উপর immediate focus দরকার।
