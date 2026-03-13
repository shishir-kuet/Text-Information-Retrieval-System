# Text Information Retrieval System — Project Document

> এই document টি বাংলা এবং English উভয় ভাষায় লেখা হয়েছে।  
> This document is written in both Bengali and English.

---

## ১. প্রজেক্ট কী? (What is this Project?)

এটি একটি **Full-Stack Information Retrieval System** — মানে একটি সম্পূর্ণ software system যেটা একটা controlled digital library (বই-এর সংগ্রহ) থেকে text search করতে পারে।

**মূল সমস্যা (Core Problem):**  
ধরো তোমার কাছে একটা line বা paragraph আছে, কিন্তু জানো না সেটা কোন বই থেকে এসেছে বা কোন page-এ আছে। এই system সেটা খুঁজে বের করবে।

**Input:** একটি text query (sentence বা paragraph)  
**Output:**
- বইয়ের নাম, লেখক, প্রকাশনা সাল
- Page number
- Relevance score (কতটা মিলেছে)
- Text snippet with highlighted matching terms

> **Algorithm:** Inverted Index + TF-IDF Ranking — কোনো AI/ML নেই, pure algorithmic approach।

---

## ২. এই প্রজেক্টে কী কী আছে? (Project Components)

### ২.১ Tech Stack

| Layer | Technology | কাজ |
|-------|-----------|------|
| **Frontend** | React + Vite | User interface |
| **Backend** | Node.js + Express | REST API, business logic |
| **Database** | MongoDB | Data storage (books, index, users) |
| **OCR Engine** | Tesseract.js | Scanned PDF থেকে text বের করা |
| **Algorithm** | Inverted Index + TF-IDF | Search ranking |
| **Auth** | JWT (JSON Web Token) | User authentication |
| **Security** | bcrypt | Password hashing |

### ২.২ Directory Structure (ফোল্ডার কাঠামো)

```
Text-Information-Retrieval-System/
├── README.md              → প্রজেক্টের সংক্ষিপ্ত পরিচিতি
├── document.md            → এই file (বিস্তারিত documentation)
├── backend/               → Express server, API routes, algorithms (এখনো empty)
├── frontend/              → React application (এখনো empty)
├── dataset/               → Book/PDF metadata (PDFs commit করা হয় না)
├── scripts/               → Utility scripts (এখনো empty)
└── docs/
    ├── problem-statement.md → সমস্যার সংজ্ঞা
    ├── requirements.md      → Functional & Non-functional requirements
    └── scope.md             → System scope এবং limitations
```

### ২.৩ System এর তিনটি প্রধান অংশ

```
[Admin uploads PDF]
       ↓
[OCR: PDF → Images → Text extraction (Tesseract)]
       ↓
[Indexer: Tokenize → Stopword removal → Build Inverted Index + TF-IDF]
       ↓
[MongoDB: Store books, pages, index]
       ↓
[User searches via React UI]
       ↓
[Backend: Query processing → TF-IDF scoring → Rank results]
       ↓
[Return: Book info + Page number + Score + Snippet]
```

---

## ৩. কীভাবে কাজ করে? (How It Works)

### ৩.১ Book Ingestion Pipeline

১. **Admin** PDF upload করে (max 25MB) — title, author, year, source সহ।  
২. System PDF-এর প্রতিটি page-কে image-এ convert করে।  
৩. **Tesseract OCR** প্রতিটি image থেকে text বের করে।  
৪. প্রতিটি page আলাদাভাবে MongoDB-তে save হয়।

### ৩.২ Indexing

Inverted index মানে হলো একটা dictionary যেখানে:
- **Key** = একটা word (term)
- **Value** = কোন কোন page-এ word টা আছে, কতবার আছে (posting list)

উদাহরণ:
```
"algorithm" → [page 12 (TF=3), page 45 (TF=1), page 78 (TF=5)]
"database"  → [page 3 (TF=2), page 12 (TF=4)]
```

Index build steps:
1. প্রতিটি page-এর text নাও
2. Tokenize করো (শব্দে ভাগ করো)
3. Lowercase করো, stopwords সরাও ("the", "is", "a" ইত্যাদি)
4. Term Frequency (TF) গণনা করো
5. Document Frequency (DF) গণনা করো
6. MongoDB-তে index save করো

### ৩.৩ Search & Ranking (TF-IDF)

**TF-IDF** মানে Term Frequency–Inverse Document Frequency।  
এটা measure করে কোনো word কোনো page-এর জন্য কতটা important।

```
TF-IDF(term, page) = TF(term, page) × log₂(N / DF(term))
```
> log base 2 ব্যবহার করা হয় — information retrieval-এর standard practice।

যেখানে:
- `TF` = ওই page-এ word টা কতবার আছে
- `N` = মোট page সংখ্যা
- `DF` = কতটা page-এ word টা আছে

Query processing:
1. User এর query tokenize ও normalize করো
2. প্রতিটি query term-এর জন্য posting list থেকে matching page খোঁজো
3. সব term-এর TF-IDF score যোগ করো
4. Score অনুযায়ী sort করো
5. Top-K results (default 5, max 20) return করো

### ৩.৪ User Roles

| Role | কী করতে পারে |
|------|-------------|
| **Admin** | PDF upload, OCR run, index build/rebuild, search logs দেখা, book management |
| **User** | Text search করা, results দেখা, page preview, search history দেখা |

### ৩.৫ Authentication

- Registration-এ email + password নেওয়া হয়
- Password bcrypt দিয়ে hash করা হয় (salt rounds ≥ 12, recommended minimum for modern hardware)
- Login করলে JWT token issue হয় (7 দিন valid)
- Protected routes-এ JWT verify করা হয়

---

## ৪. Functional Requirements — কী কী feature আছে?

### User Features
- **FR-1:** Registration (name, email, password)
- **FR-2:** Login → JWT token
- **FR-3:** Role-based access (Admin / User)
- **FR-4:** Text-based search (sentence বা paragraph দিয়ে)
- **FR-5:** Top-K results দেখা (book info, page, score, snippet) — default K=5, max K=20, configurable via query parameter
- **FR-6:** Full page preview with highlighted terms
- **FR-7:** Search history (last 50 searches)

### Admin Features
- **FR-8:** PDF upload with metadata (max 25MB, configurable via environment variable)
- **FR-9:** Automatic OCR text extraction
- **FR-10:** Inverted index build/rebuild
- **FR-11:** Book management (view, filter by status, search)
- **FR-12:** Search logs & analytics
- **FR-13:** All searches logged (user, query, timestamp, results)

---

## ৫. Non-Functional Requirements — কী কী performance দরকার?

| Category | Requirement |
|----------|------------|
| **Performance** | 95% search queries < 2 seconds |
| **Scalability** | 100–1000 books support করতে পারবে |
| **Concurrency** | কমপক্ষে 10 concurrent user handle করবে |
| **Security** | JWT auth, bcrypt hashing (salt rounds ≥ 12), rate limiting (120 req/min/IP for search; lower limits for upload/OCR operations) |
| **Reliability** | Invalid PDF gracefully handle, no duplicate books/pages |
| **Maintainability** | Clean modular code, no hardcoded secrets |
| **Testability** | Unit tests for tokenizer/indexer/scorer, integration tests |
| **Usability** | Responsive UI, user-friendly error messages |

---

## ৬. Scope — কী আছে, কী নেই?

### In Scope (যা করা হবে)
- Book management (PDF upload, metadata)
- OCR text extraction (Tesseract)
- Inverted index building
- TF-IDF search ranking
- User authentication & role-based access
- Search history & admin analytics
- Performance testing & evaluation

### Out of Scope (যা করা হবে না)
- Internet বা external web page search
- Mobile application
- Real-time collaboration
- Advanced NLP (summarization, translation)
- Handwritten text recognition
- Copyright-violating public book distribution

### Limitations (সীমাবদ্ধতা)
- OCR accuracy poor quality scan-এ কমে যাবে
- TF-IDF lexical match করে — paraphrased text match নাও করতে পারে
- Index rebuild করতে হয় নতুন book যোগের পর (real-time নয়)
- শুধু English content support করে OCR ও search-এর জন্য (system UI এবং documentation Bengali ও English উভয়ে লেখা যাবে)
- Complex layouts (tables, math symbols) ঠিকমতো OCR নাও হতে পারে

---

## ৭. সমস্যাসমূহ (Problems & Issues)

### ৭.১ Critical Issues (গুরুতর সমস্যা)

**সমস্যা ১: Code Implementation নেই**
- `backend/`, `frontend/`, `dataset/`, `scripts/` — সব directory তে শুধু `.gitkeep` file আছে।
- কোনো actual source code এখনো লেখা হয়নি।
- **Status:** 🔴 Critical — implement করতে হবে।

**সমস্যা ২: Tech Stack Contradiction (Tech Stack-এ দ্বন্দ্ব)**
- README.md বলছে: **Node.js/Express + React**
- কিন্তু requirements.md-এ mention আছে Python-based approach (app.py reference)।
- **Status:** 🔴 এটা clarify করে fix করতে হবে।

**সমস্যা ৩: Git Workflow Professional নয়**
- শুধু একটি branch আছে: `copilot/integrate-premium-copilot`
- মাত্র ২টি commit।
- Feature branches, PRs, code reviews — কিছুই নেই।
- **Status:** 🟡 Team workflow improve করতে হবে।

### ৭.২ Requirements Issues

**সমস্যা ৪: Performance Target কঠিন হতে পারে**
- NFR-1: 95% queries < 2 seconds — 1000 বইয়ের জন্য caching/optimization ছাড়া কঠিন।
- কোনো caching strategy mention নেই।

**সমস্যা ৫: Missing Implementation Details**
- Tokenization strategy কী? (Porter stemmer? Simple split?)
- Stopword list কোথা থেকে আসবে?
- Snippet generation algorithm কী?
- Database schema design নেই।
- API endpoint specifications নেই।

**সমস্যা ৬: OCR Processing Scope Underestimated**
- OCR computationally expensive — large PDF-এর জন্য async processing দরকার।
- Image preprocessing pipeline (deskew, denoise, binarize) mention নেই।
- Corrupted বা encrypted PDF handle করার strategy নেই।

**সমস্যা ৭: Testing Requirements অস্পষ্ট**
- NFR-17/18/19 testing mention করেছে কিন্তু:
  - কোনো test framework specify করা নেই।
  - Baseline accuracy targets নেই।
  - কোনো test example নেই।

**সমস্যা ৮: Deployment Plan নেই**
- Docker configuration নেই।
- Deployment instructions নেই।
- Environment variable examples নেই।

**সমস্যা ৯: Error Handling Strategy অস্পষ্ট**
- OCR failure হলে কী হবে?
- Partial index corruption থেকে কীভাবে recover করবে?
- Failed upload-এ retry logic কী?

**সমস্যা ১০: Database Scalability**
- Raw OCR text + snippets + index data MongoDB-তে রাখলে memory-intensive হতে পারে।
- Compression বা pagination strategy নেই।
- Query optimization plan নেই।

---

## ৮. Recommended Next Steps (পরবর্তী পদক্ষেপ)

1. **Tech stack clarify করো** — Node.js/Express নাকি Python? Final decision নাও।
2. **Database schema design করো** — Users, Books, Pages, Index, SearchLogs collection গুলোর structure ঠিক করো।
3. **API endpoints define করো** — সব routes document করো আগে code করার আগে।
4. **Backend skeleton বানাও** — Express server, MongoDB connection, basic auth দিয়ে শুরু করো।
5. **Algorithm আগে implement করো** — Tokenizer → Indexer → TF-IDF Scorer।
6. **Git workflow ঠিক করো** — Feature branches তৈরি করো, PR review শুরু করো।
7. **Performance benchmarking** — Early stage থেকেই latency measure করো।
8. **Async OCR processing** — Large PDF-এর জন্য queue-based processing বানাও।

---

## ৯. Success Criteria (সাফল্যের মানদণ্ড)

- [ ] Known query দিলে সঠিক book + page return করে
- [ ] Dataset বাড়ার সাথে search latency acceptable থাকে
- [ ] Index build time ও storage usage measure ও report করা হয়
- [ ] GitHub-এ clear workflow: branches, PRs, code reviews, issues
- [ ] Comprehensive documentation ও professional presentation

---

## ১০. Team Information

| Member | Responsibility |
|--------|---------------|
| **Member 1** | Backend + Algorithms (OCR pipeline, Inverted Index, TF-IDF, API) |
| **Member 2** | Frontend + Auth + Documentation (React UI, JWT, bcrypt, docs) |

---

*Document last updated: March 2026*  
*Project status: 🚧 In Development — Documentation phase complete, Implementation pending*
