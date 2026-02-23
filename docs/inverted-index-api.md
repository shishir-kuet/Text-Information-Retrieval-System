# Inverted Index API Documentation

This module builds and maintains an inverted index for full-text search using TF-IDF ranking algorithm.

## Architecture

```
Processed Books → Tokenization → Stemming → Inverted Index
                       ↓              ↓            ↓
                  Stopword      Porter      IndexTerm
                  Removal      Stemmer      Collection
```

## Text Processing Pipeline

### 1. Tokenization

- Convert text to lowercase
- Split into words using natural.WordTokenizer
- Filter alphabetic tokens (length ≥ 2)

### 2. Stopword Removal

- Remove common English stopwords (the, is, at, which, etc.)
- Uses 'stopword' library

### 3. Stemming

- Apply Porter Stemmer algorithm
- Reduces words to their root form (e.g., "running" → "run")

### 4. Index Building

- Calculate term frequency (TF) for each term per page
- Store in IndexTerm collection with document frequency (DF)
- Create postings list: term → [{pageId, tf}]

---

## API Endpoints

### 1. Build Index for Specific Book

**Endpoint:** `POST /api/index/build/:id`

**Description:** Build inverted index for a specific book that has been processed with OCR.

**URL Parameters:**

- `id` (string, required): Book MongoDB ObjectId

**Prerequisites:**

- Book must have status = "processed"
- Book pages must exist in database

**Example:**

```bash
curl -X POST http://localhost:5000/api/index/build/65f1a2b3c4d5e6f7a8b9c0d1
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Index built successfully for book",
  "data": {
    "bookId": "65f1a2b3c4d5e6f7a8b9c0d1",
    "bookTitle": "Sample Book",
    "totalPages": 150,
    "termsAdded": 2547,
    "termsUpdated": 1203,
    "totalTokens": 45230,
    "uniqueTerms": 3750
  }
}
```

**Book Status Changes:**

- Before: `status: "processed"`
- During: `status: "indexing"`
- After: `status: "indexed"`

**Error Response (400 Bad Request):**

```json
{
  "success": false,
  "message": "Book status is 'uploaded'. Must be 'processed' to build index."
}
```

---

### 2. Build Index for All Books

**Endpoint:** `POST /api/index/build-all`

**Description:** Build inverted index for all books with status = "processed".

**Example:**

```bash
curl -X POST http://localhost:5000/api/index/build-all
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Index built successfully for all books",
  "data": {
    "booksIndexed": 3,
    "totalPages": 450,
    "totalTokens": 135690,
    "totalUniqueTerms": 8247,
    "termsAdded": 8247,
    "termsUpdated": 3586,
    "books": [
      {
        "bookId": "65f1a2b3c4d5e6f7a8b9c0d1",
        "title": "Book 1",
        "pages": 150,
        "tokens": 45230
      },
      {
        "bookId": "65f1a2b3c4d5e6f7a8b9c0d2",
        "title": "Book 2",
        "pages": 200,
        "tokens": 60340
      },
      {
        "bookId": "65f1a2b3c4d5e6f7a8b9c0d3",
        "title": "Book 3",
        "pages": 100,
        "tokens": 30120
      }
    ]
  }
}
```

**Response when no books to index:**

```json
{
  "success": true,
  "message": "Index built successfully for all books",
  "data": {
    "message": "No processed books found",
    "booksIndexed": 0
  }
}
```

---

### 3. Rebuild Entire Index

**Endpoint:** `POST /api/index/rebuild`

**Description:** Clear existing index and rebuild from scratch for all processed books.

**Warning:** This operation deletes all existing IndexTerm documents!

**Example:**

```bash
curl -X POST http://localhost:5000/api/index/rebuild
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Index rebuilt successfully",
  "data": {
    "message": "Index rebuilt successfully",
    "clearedTerms": 8247,
    "booksIndexed": 3,
    "totalPages": 450,
    "totalTokens": 135690,
    "totalUniqueTerms": 8247,
    "termsAdded": 8247,
    "termsUpdated": 0
  }
}
```

**Use Cases:**

- After changing tokenization algorithm
- After updating stopword list
- Fixing corrupted index data
- Initial setup after importing books

---

### 4. Get Index Statistics

**Endpoint:** `GET /api/index/stats`

**Description:** Retrieve statistics about the inverted index.

**Example:**

```bash
curl http://localhost:5000/api/index/stats
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "totalTerms": 8247,
    "indexedBooks": 3,
    "totalBooks": 5,
    "totalPages": 450,
    "indexCoverage": "60.00%",
    "topTermsByDocFrequency": [
      { "term": "inform", "df": 245 },
      { "term": "system", "df": 198 },
      { "term": "data", "df": 187 },
      { "term": "search", "df": 165 },
      { "term": "retriev", "df": 152 },
      { "term": "text", "df": 143 },
      { "term": "user", "df": 132 },
      { "term": "document", "df": 128 },
      { "term": "model", "df": 121 },
      { "term": "queri", "df": 115 }
    ]
  }
}
```

**Statistics Explained:**

- `totalTerms`: Number of unique terms in index
- `indexedBooks`: Books with status = "indexed"
- `totalBooks`: All books in database
- `totalPages`: Total pages across all books
- `indexCoverage`: Percentage of books that are indexed
- `topTermsByDocFrequency`: Most common terms (appearing in most pages)

---

### 5. Remove Book from Index

**Endpoint:** `DELETE /api/index/book/:id`

**Description:** Remove all index entries for a specific book.

**URL Parameters:**

- `id` (string, required): Book MongoDB ObjectId

**Example:**

```bash
curl -X DELETE http://localhost:5000/api/index/book/65f1a2b3c4d5e6f7a8b9c0d1
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Book removed from index",
  "data": {
    "removedTerms": 547
  }
}
```

**What happens:**

1. Finds all pages belonging to the book
2. Removes postings for those pages from IndexTerm documents
3. Deletes IndexTerm documents that have no remaining postings
4. Returns count of terms completely removed

**Use Cases:**

- Before deleting a book
- Before re-indexing a book with updated content

---

## Data Structures

### IndexTerm Model

```javascript
{
  term: String (unique, lowercase),    // Stemmed term
  df: Number,                           // Document frequency (number of pages)
  postings: [                           // Posting list
    {
      pageId: ObjectId (ref: Page),    // Reference to page
      tf: Number                        // Term frequency in that page
    }
  ]
}
```

**Example:**

```json
{
  "_id": "65f1a2b3c4d5e6f7a8b9c0e1",
  "term": "inform",
  "df": 3,
  "postings": [
    { "pageId": "65f1a2b3c4d5e6f7a8b9c0f1", "tf": 5 },
    { "pageId": "65f1a2b3c4d5e6f7a8b9c0f2", "tf": 3 },
    { "pageId": "65f1a2b3c4d5e6f7a8b9c0f3", "tf": 7 }
  ]
}
```

---

## TF-IDF Algorithm (For Search - Step 6)

### Term Frequency (TF)

```
TF(term, page) = frequency of term in page
```

### Inverse Document Frequency (IDF)

```
IDF(term) = log(total pages / df)
```

Where:

- `total pages` = total number of pages in corpus
- `df` = document frequency (number of pages containing term)

### TF-IDF Score

```
TF-IDF(term, page) = TF(term, page) × IDF(term)
```

**Purpose:** Terms that appear frequently in a document but rarely across all documents get higher scores.

---

## Tokenization Examples

### Example 1: Basic Text

**Input:**

```
"The Information Retrieval System provides fast search capabilities."
```

**Processing Steps:**

1. Lowercase: `"the information retrieval system provides fast search capabilities."`
2. Tokenize: `["the", "information", "retrieval", "system", "provides", "fast", "search", "capabilities"]`
3. Filter: `["the", "information", "retrieval", "system", "provides", "fast", "search", "capabilities"]`
4. Remove stopwords: `["information", "retrieval", "system", "provides", "fast", "search", "capabilities"]`
5. Stem: `["inform", "retriev", "system", "provid", "fast", "search", "capabl"]`

**Result:** 7 unique terms

---

### Example 2: Technical Text

**Input:**

```
"Running queries on databases requires optimization. The query runner optimizes queries efficiently."
```

**After Processing:**

```
["run", "queri", "databas", "requir", "optim", "queri", "runner", "optim", "queri", "effici"]
```

**Term Frequencies:**

- `queri`: 3
- `optim`: 2
- `run`: 1
- `runner`: 1
- `databas`: 1
- `requir`: 1
- `effici`: 1

---

## Performance Considerations

### Indexing Time Estimates

- **Small book (50 pages):** ~2-5 seconds
- **Medium book (200 pages):** ~10-20 seconds
- **Large book (500 pages):** ~30-60 seconds
- **30 books (~3000 pages):** ~10-15 minutes

### Optimization Tips

1. **Batch Processing:** Index multiple books in parallel (future enhancement)
2. **Incremental Updates:** Only re-index changed pages
3. **Caching:** Cache tokenizer and stemmer instances
4. **Database Indexes:** Ensure IndexTerm.term has index
5. **Bulk Operations:** Use MongoDB bulk writes for postings updates

---

## Error Handling

### Common Errors

**1. Book Not Processed**

```json
{
  "success": false,
  "message": "Book status is 'uploaded'. Must be 'processed' to build index."
}
```

**Solution:** Wait for OCR processing to complete or check book status.

**2. No Pages Found**

```json
{
  "success": false,
  "message": "No pages found for this book"
}
```

**Solution:** Verify book was processed successfully and pages exist.

**3. Book Not Found**

```json
{
  "success": false,
  "message": "Book not found"
}
```

**Solution:** Check book ID is correct.

---

## Testing

### Run Verification Script:

```bash
npm run check:index
```

### Run Comprehensive Tests:

```bash
npm run test:index
```

### Manual Testing Flow:

1. **Upload and process a book:**

   ```bash
   curl -X POST http://localhost:5000/api/books/upload \
     -F "pdf=@sample.pdf" \
     -F "title=Test Book"
   ```

2. **Wait for processing to complete, then build index:**

   ```bash
   curl -X POST http://localhost:5000/api/index/build/{bookId}
   ```

3. **Check index statistics:**

   ```bash
   curl http://localhost:5000/api/index/stats
   ```

4. **View indexed terms (MongoDB):**
   ```javascript
   db.indexterms.find().limit(10).pretty();
   ```

---

## Future Enhancements

- [ ] Parallel indexing for multiple books
- [ ] Progress tracking with WebSocket updates
- [ ] Custom stopword lists per language
- [ ] Bigram/trigram support for phrase search
- [ ] Index compression for storage efficiency
- [ ] Incremental index updates (only changed content)
- [ ] Multi-language support (language detection)
- [ ] Synonym expansion during indexing
- [ ] Named entity recognition integration
- [ ] Index versioning and rollback
