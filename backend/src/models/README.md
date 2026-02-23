# Database Models

This directory contains MongoDB schemas for the Text Information Retrieval System.

## Models Overview

### 1. Book Model
Stores book metadata and processing status.

**Fields:**
- `title` (String, required, indexed): Book title
- `author` (String, indexed): Author name (default: "Unknown")
- `year` (Number): Publication year
- `source` (String): Original source or collection
- `fileName` (String, required, unique): Original PDF filename
- `totalPages` (Number): Total page count
- `status` (Enum): Processing status - `uploaded`, `processing`, `processed`, `indexed`, `failed`
- `ocrCompleted` (Boolean): OCR completion flag
- `ocrError` (String): OCR error message if failed
- `timestamps`: Auto-generated `createdAt` and `updatedAt`

**Indexes:**
- Text index on `title` and `author` for search
- Index on `status` for filtering
- Unique index on `fileName`

---

### 2. Page Model
Stores extracted text content for each page.

**Fields:**
- `bookId` (ObjectId → Book, required, indexed): Parent book reference
- `pageNumber` (Number, required): Page number (1-based)
- `text` (String, required): Extracted text from OCR
- `tokenCount` (Number): Number of tokens in text
- `ocrConfidence` (Number, 0-100): OCR confidence score
- `timestamps`: Auto-generated `createdAt` and `updatedAt`

**Indexes:**
- Compound unique index on `(bookId, pageNumber)` to prevent duplicates
- Index on `bookId` for efficient page retrieval per book

**Relationships:**
- Each Page belongs to one Book

---

### 3. User Model
Stores user authentication and role information.

**Fields:**
- `name` (String, required): User full name
- `email` (String, required, unique, indexed): User email (lowercase)
- `passwordHash` (String, required): Hashed password (hidden in JSON)
- `role` (Enum, indexed): User role - `admin` or `user`
- `isActive` (Boolean): Account status
- `timestamps`: Auto-generated `createdAt` and `updatedAt`

**Indexes:**
- Unique index on `email`
- Index on `role` for filtering

**Security:**
- Password hash excluded from JSON responses via `toJSON` transform

---

### 4. SearchLog Model
Tracks search queries and results for analytics.

**Fields:**
- `userId` (ObjectId → User, indexed): User who performed search (nullable for anonymous)
- `query` (String, required): Search query text
- `topResults` (Array): Top search results
  - `bookId` (ObjectId → Book): Matched book
  - `pageId` (ObjectId → Page): Matched page
  - `score` (Number): TF-IDF relevance score
- `resultCount` (Number): Total results returned
- `executionTimeMs` (Number): Query execution time in milliseconds
- `timestamps`: Auto-generated `createdAt` and `updatedAt`

**Indexes:**
- Index on `createdAt` (descending) for recent searches
- Compound index on `(userId, createdAt)` for user history

**Relationships:**
- Each SearchLog optionally belongs to one User
- Each result references Book and Page

---

### 5. IndexTerm Model
Stores the inverted index for full-text search with TF-IDF.

**Fields:**
- `term` (String, required, unique, lowercase, indexed): Indexed term
- `df` (Number, required): Document frequency (number of pages containing term)
- `postings` (Array): Posting list
  - `pageId` (ObjectId → Page, required): Page containing term
  - `tf` (Number, required): Term frequency in that page
- `timestamps`: Auto-generated `createdAt` and `updatedAt`

**Indexes:**
- Unique index on `term` for fast lookups
- Text index on `term` for autocomplete/suggestions

**Relationships:**
- Each posting references one Page
- Used for TF-IDF ranking algorithm

**TF-IDF Calculation:**
```
TF(term, page) = (frequency of term in page) / (total terms in page)
IDF(term) = log(total pages / df)
TF-IDF(term, page) = TF(term, page) × IDF(term)
```

---

## Usage

Import all models from the index:
```javascript
const { Book, Page, User, SearchLog, IndexTerm } = require('./models');
```

Or import individually:
```javascript
const Book = require('./models/Book');
```

## Testing

Run model verification:
```bash
npm run check:models
```

This verifies:
- All model files exist
- Models load without errors
- Schemas are properly defined
- Relationships are correctly configured
- Indexes are properly set up
