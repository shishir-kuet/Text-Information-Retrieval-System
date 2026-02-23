# Search API Documentation

## Overview

The Search API provides full-text search functionality using TF-IDF (Term Frequency-Inverse Document Frequency) ranking algorithm.

## Base URL

```
http://localhost:5000/api
```

## Endpoints

### 1. Search Documents

**POST** `/search`

Search for documents matching a query using TF-IDF scoring.

#### Request Body

```json
{
  "query": "information retrieval",
  "limit": 10,
  "minScore": 0.01,
  "books": ["bookId1", "bookId2"]
}
```

| Field    | Type   | Required | Default | Description                         |
| -------- | ------ | -------- | ------- | ----------------------------------- |
| query    | string | Yes      | -       | Search query string                 |
| limit    | number | No       | 10      | Maximum number of results to return |
| minScore | number | No       | 0.01    | Minimum TF-IDF score threshold      |
| books    | array  | No       | null    | Filter results by specific book IDs |

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "query": "information retrieval",
    "processedQuery": ["inform", "retriev"],
    "results": [
      {
        "pageId": "699cde1e...",
        "pageNumber": 1,
        "bookId": "699cde09...",
        "bookTitle": "IR Textbook",
        "bookAuthor": "AI Developers",
        "score": 2.4567,
        "termMatches": [
          {
            "term": "inform",
            "tf": 3,
            "idf": 0.4055,
            "tfidf": 1.2165
          },
          {
            "term": "retriev",
            "tf": 2,
            "idf": 0.6201,
            "tfidf": 1.2402
          }
        ],
        "snippet": "...Introduction to **Information** **Retrieval** is the science of searching...",
        "tokenCount": 87
      }
    ],
    "totalResults": 5,
    "returnedResults": 1
  }
}
```

#### Response Fields

| Field           | Type   | Description                         |
| --------------- | ------ | ----------------------------------- |
| query           | string | Original search query               |
| processedQuery  | array  | Stemmed and filtered query terms    |
| results         | array  | Array of matching pages             |
| totalResults    | number | Total matching pages (before limit) |
| returnedResults | number | Number of results returned          |

#### Result Object Fields

| Field       | Type   | Description                                        |
| ----------- | ------ | -------------------------------------------------- |
| pageId      | string | Page MongoDB ObjectId                              |
| pageNumber  | number | Page number in the book                            |
| bookId      | string | Book MongoDB ObjectId                              |
| bookTitle   | string | Title of the book                                  |
| bookAuthor  | string | Author of the book                                 |
| score       | number | TF-IDF relevance score                             |
| termMatches | array  | Breakdown of score per term                        |
| snippet     | string | Text excerpt with highlighted terms (\*\* markers) |
| tokenCount  | number | Total tokens in the page                           |

#### Error Response (400 Bad Request)

```json
{
  "success": false,
  "message": "Query parameter is required"
}
```

### 2. Get Search Statistics

**GET** `/search/stats`

Get statistics about the search system.

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "totalBooks": 2,
    "indexedBooks": 1,
    "totalPages": 5,
    "totalTerms": 150,
    "searchReady": true
  }
}
```

| Field        | Type    | Description                     |
| ------------ | ------- | ------------------------------- |
| totalBooks   | number  | Total books in database         |
| indexedBooks | number  | Books with inverted index built |
| totalPages   | number  | Total pages in database         |
| totalTerms   | number  | Total unique terms in index     |
| searchReady  | boolean | Whether search is ready to use  |

## TF-IDF Algorithm

### How It Works

1. **Query Processing**
   - Tokenize query text
   - Remove stopwords (the, a, an, etc.)
   - Apply Porter Stemming (information → inform)

2. **Term Lookup**
   - Find each query term in the inverted index
   - Retrieve posting lists (which pages contain the term)

3. **TF-IDF Calculation**
   - For each page containing query terms:
   - `TF` = Term Frequency (how many times term appears in page)
   - `DF` = Document Frequency (how many pages contain the term)
   - `IDF` = Inverse Document Frequency = `log(totalPages / DF)`
   - `TF-IDF` = `TF × IDF`

4. **Score Aggregation**
   - Sum TF-IDF scores for all query terms in each page
   - `PageScore = ∑(TF-IDF for each query term)`

5. **Ranking**
   - Sort pages by total score (descending)
   - Return top-K results

### Example Calculation

Given:

- Total pages in corpus: `N = 5`
- Query: "information retrieval"
- Processed: ["inform", "retriev"]

For Page 1:

- Term "inform": TF=3, DF=2, IDF=log(5/2)=0.9163
  - TF-IDF = 3 × 0.9163 = 2.7489
- Term "retriev": TF=2, DF=3, IDF=log(5/3)=0.5108
  - TF-IDF = 2 × 0.5108 = 1.0216
- **Total Score = 2.7489 + 1.0216 = 3.7705**

### Score Interpretation

| Score Range | Relevance                   |
| ----------- | --------------------------- |
| > 5.0       | Highly relevant             |
| 2.0 - 5.0   | Moderately relevant         |
| 0.5 - 2.0   | Somewhat relevant           |
| 0.01 - 0.5  | Weakly relevant             |
| < 0.01      | Not relevant (filtered out) |

## Usage Examples

### Example 1: Basic Search

```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "information retrieval"}'
```

### Example 2: Search with Limit

```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "inverted index", "limit": 5}'
```

### Example 3: Search Specific Books

```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "tf-idf algorithm",
    "books": ["699cde090b053d9c7b55e5ff"]
  }'
```

### Example 4: High-Quality Results Only

```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "search ranking",
    "minScore": 1.0
  }'
```

### Example 5: Get Search Stats

```bash
curl http://localhost:5000/api/search/stats
```

## Snippet Highlighting

Snippets contain text excerpts with query terms highlighted using `**` markers:

```
"...Introduction to **Information** **Retrieval** is the science..."
```

- Query terms are stemmed before matching
- All variations of the term are highlighted (information, informational, etc.)
- Snippet centers around the first occurrence of a query term
- Maximum snippet length: 200 characters

## Error Handling

### Common Errors

| Status | Message                     | Solution                        |
| ------ | --------------------------- | ------------------------------- |
| 400    | Query parameter is required | Provide a query in request body |
| 404    | No documents found          | Index is empty or no matches    |
| 500    | Search error                | Check server logs               |

### No Results Scenarios

1. **No valid search terms**
   - All query words are stopwords
   - Response: `{ results: [], message: "No valid search terms..." }`

2. **Terms not in index**
   - Query terms don't exist in any document
   - Response: `{ results: [], message: "No documents found..." }`

3. **Below minimum score**
   - Matches exist but scores too low
   - Response: `{ results: [], totalResults: 0 }`

## Performance Considerations

### Query Processing Time

- Typical: 10-50ms for small corpus (<100 pages)
- Scales logarithmically with corpus size

### Optimization Tips

1. Use specific queries (2-4 terms optimal)
2. Set appropriate `minScore` to filter weak matches
3. Use `limit` to control result size
4. Filter by `books` to search specific subset

## Testing Workflow

1. **Upload and index a book**

   ```bash
   # Upload PDF
   curl -X POST -F "pdf=@sample.pdf" -F "title=Book Title" \
     http://localhost:5000/api/books/upload

   # Build index
   curl -X POST http://localhost:5000/api/index/build/{bookId}
   ```

2. **Verify search readiness**

   ```bash
   curl http://localhost:5000/api/search/stats
   # Check: searchReady should be true
   ```

3. **Perform searches**

   ```bash
   curl -X POST http://localhost:5000/api/search \
     -H "Content-Type: application/json" \
     -d '{"query": "your search terms"}'
   ```

4. **Analyze results**
   - Check `score` values (higher = more relevant)
   - Review `termMatches` for scoring breakdown
   - Examine `snippet` for context

## Integration with Frontend

### React Example

```javascript
const search = async (query) => {
  const response = await fetch("http://localhost:5000/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, limit: 10 }),
  });

  const data = await response.json();
  return data.data.results;
};
```

### Display Results

```javascript
{
  results.map((result) => (
    <div key={result.pageId}>
      <h3>
        {result.bookTitle} - Page {result.pageNumber}
      </h3>
      <p>Score: {result.score.toFixed(2)}</p>
      <p
        dangerouslySetInnerHTML={{
          __html: result.snippet.replace(/\*\*(.*?)\*\*/g, "<mark>$1</mark>"),
        }}
      />
    </div>
  ));
}
```

## Next Steps

After implementing Search API:

1. Test with various queries
2. Analyze result relevance
3. Tune `minScore` threshold
4. Consider adding:
   - Query expansion (synonyms)
   - Phrase matching
   - Boolean operators (AND, OR, NOT)
   - Fuzzy matching
   - Date/author filters
