# Problem Statement

## Title

**Text Information Retrieval System**  
(Indexed Search Engine for Controlled Digital Library)

## Background

Universities and institutions maintain large digital collections of books. Often a user may possess only a short line or paragraph of text without knowing which book it belongs to or which page it appears on. Manual searching across many books is time-consuming and unreliable.

## Problem Definition

Given an input text query (a sentence or paragraph), the system must identify the most relevant source locations inside a controlled digital library, and return the corresponding:

- Book information (title, author, year)
- Page number
- Relevance score
- Text snippet with highlights

## Primary Objective

Design and develop a full-stack information retrieval system that indexes a controlled collection of books and retrieves the most relevant pages for a given text query using **inverted index** and **TF-IDF ranking** (non-AI/ML approach).

## Why This is a System Engineering Project

This project encompasses:

- Dataset ingestion and processing
- **OCR (Optical Character Recognition)** for scanned document text extraction
- Image preprocessing for OCR optimization
- Database design and optimization
- Indexing algorithms (inverted index)
- Search ranking algorithms (TF-IDF)
- API development (RESTful)
- UI/UX development (React)
- Security (authentication, role-based access)
- Testing (unit, integration, performance)
- Performance evaluation and analysis
- Professional project management workflow (Git, PRs, code reviews)

## Stakeholders

1. **Admin**: Manages book ingestion and indexing
2. **User**: Searches by text and views results
3. **Supervisor/Examiner**: Evaluates engineering process, documentation, and outcomes

## Success Criteria

1. Returns correct book + page for known queries
2. Search latency remains acceptable as the number of pages increases
3. Index build time and storage usage are measured and reported
4. Clear GitHub workflow evidence: branches, PRs, code reviews, commits, issues
5. Comprehensive documentation and professional presentation

## Constraints

- Must use algorithm-based approach (no AI/ML models)
- Must demonstrate professional teamwork through GitHub
- Must show engineering depth, not just working code
- Must include performance analysis and scalability testing
