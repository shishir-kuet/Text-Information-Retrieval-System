# Problem Statement

## Title

**Text Information Retrieval System**  
(Indexed Search Engine for Controlled Digital Library)

## Background

Universities and institutions maintain large digital collections of books. Often a user may possess only a short line or paragraph of text without knowing which book it belongs to or which page it appears on. Manual searching across many books is time-consuming and unreliable.

## Problem Definition

Given an input text query (a sentence or paragraph), the system must identify the most relevant source locations inside a controlled digital library, and return the corresponding:

- Book title and domain
- Page number
- Relevance score
- Text snippet (preview)

## Primary Objective

Design and develop an information retrieval system that indexes a controlled collection of books and retrieves the most relevant pages for a given text query using an **inverted index** and **BM25 ranking** (non-AI/ML approach).

## Why This is a System Engineering Project

This project encompasses:

- Dataset ingestion and processing (PDF text extraction)
- **OCR (Optical Character Recognition)** for scanned document text extraction
- Database design and optimisation (MongoDB)
- Indexing algorithms (inverted index with BM25)
- Search ranking algorithms (BM25 + proximity scoring + exact-phrase boost)
- Python backend architecture (services, models, config layers)
- Testing (unit and integration)
- Performance evaluation and analysis
- Professional project management workflow (Git, branches, commits)

## Stakeholders

1. **Admin**: Manages book ingestion and index building via CLI scripts
2. **User**: Searches by text query via the CLI search interface
3. **Supervisor/Examiner**: Evaluates engineering process, documentation, and outcomes

## Success Criteria

1. Returns correct book + page for known queries
2. Search latency is below 2 seconds for typical queries on the full collection
3. Index build time and storage usage are measured and reported
4. Codebase is modular, tested, and follows professional structure
5. Comprehensive documentation maintained in the `docs/` folder

## Constraints

- Must use algorithm-based approach (no AI/ML models)
- Must demonstrate a professional, layered Python codebase
- Must include unit tests and integration tests
- Must include performance analysis and scalability considerations
