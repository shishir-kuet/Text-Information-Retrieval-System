# Database Schema (MongoDB)

## Collections
- `books`
- `pages`
- `users`
- `search_logs`

## Design Rule
Compatible schema evolution.
- Preserve existing `books` and `pages` data.
- Extend fields safely.

## books
Purpose: metadata about each book and its ingestion status.

Recommended indexes:
- `book_id` unique
- `domain` index
- `status` index

Example:
```json
{
  "book_id": 1,
  "title": "Computer Algorithms",
  "domain": "Computer Science",
  "file_name": "Computer Algorithms.pdf",
  "stored_file_name": "book_001.pdf",
  "file_path": "backend/books/Computer Science/book_001.pdf",
  "num_pages": 777,
  "file_size_mb": 28.64,
  "status": "indexed",
  "ingestion_method": "ocr",
  "is_downloadable": true,
  "date_added": "2026-03-02 00:52:29",
  "updated_at": "2026-03-02 00:52:29"
}
```

Statuses:
- `uploaded`
- `processed`
- `indexed`

## pages
Purpose: page-wise extracted text for indexing and ranking.

Recommended indexes:
- `page_id` unique
- (`book_id`, `page_number`) unique
- `book_id` index

Example:
```json
{
  "page_id": "1_1",
  "book_id": 1,
  "page_number": 1,
  "display_page_number": "1",
  "text_content": "...",
  "word_count": 420,
  "char_count": 2500,
  "token_count": 390,
  "created_at": "2026-03-02 00:52:29"
}
```

## users
Purpose: authentication/authorization.

Recommended indexes:
- `user_id` unique
- `email` unique
- `role` index

Example:
```json
{
  "user_id": 1,
  "name": "User Name",
  "email": "user@example.com",
  "password_hash": "...",
  "role": "user",
  "created_at": "2026-03-14 10:00:00",
  "updated_at": "2026-03-14 10:00:00"
}
```

## search_logs
Purpose: user history + analytics.

Recommended indexes:
- `log_id` unique
- `user_id` index
- `created_at` index

Example:
```json
{
  "log_id": 1,
  "user_id": 1,
  "query_text": "dynamic programming",
  "normalized_query": ["dynamic", "programming"],
  "total_results": 5,
  "top_results": [
    {"book_id": 1, "page_id": "1_245", "page_number": 245, "score": 18.2}
  ],
  "latency_ms": 90,
  "created_at": "2026-03-14 11:20:00"
}
```

Guest searches can be stored with `user_id=null`.
