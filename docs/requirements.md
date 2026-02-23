# System Requirements

## Functional Requirements (FR)

### User Management

**FR-1: User Registration**

- Users can register with name, email, and password
- Email must be unique
- Password must be securely hashed
- Default role: "user"

**FR-2: User Login**

- Users can login with email and password
- System generates JWT token for authenticated sessions
- Token expires after 7 days

**FR-3: Role Management**

- Two roles: Admin and User
- Admins have access to management features
- Users have access to search features

### Search Functionality

**FR-4: Text-Based Search**

- User can submit a sentence/paragraph as query
- System processes and normalizes the query
- Minimum 1 character required

**FR-5: Search Results**

- System returns top-K matches (default K=5, configurable up to 20)
- Each result includes:
  - Book title, author, year
  - Page number
  - Relevance score
  - Text snippet with context
  - Matched terms list

**FR-6: Page Preview**

- User can click a result to open full page text
- System highlights matched query terms
- Shows book metadata and page number

**FR-7: Search History**

- Logged-in users can view their past queries
- Shows query text, timestamp, and number of results
- Limited to last 50 searches

### Admin Features

**FR-8: Book Upload**

- Admin can upload PDF file with metadata:
  - Title (required)
  - Author (optional)
  - Year (optional)
  - Source (optional)
- Maximum file size: 25MB
- Only PDF format accepted

**FR-9: OCR Text Extraction**

- System automatically performs OCR on scanned PDF pages
- Converts PDF pages to images first
- Applies OCR (Tesseract) to extract text from each page
- Handles multi-page PDFs automatically
- Stores each page as separate document with extracted text
- Calculates token count per page
- Reports OCR confidence/quality metrics
- Handles OCR errors gracefully (logs unreadable pages)

**FR-10: Index Management**

- Admin can build/rebuild inverted index
- System process all pages and creates:
  - Term dictionary
  - Posting lists (term → page mappings)
  - Term frequency (TF) per page
  - Document frequency (DF) per term
- Shows build time and total terms indexed

**FR-11: Book Management**

- Admin can view all books with metadata
- Filter books by status (uploaded/processed/indexed)
- Search books by title or author

**FR-12: Search Logs & Analytics**

- Admin can view all search logs
- Filter logs by query text
- Shows user, query, timestamp, and top results

### System Logging

**FR-13: Search Logging**

- System records every search with:
  - User ID (if logged in)
  - Query text
  - Timestamp
  - Top results (book, page, score)

---

## Non-Functional Requirements (NFR)

### Performance

**NFR-1: Search Response Time**

- Search queries should return results within 2 seconds for 95% of requests
- Performance should remain acceptable as dataset grows
- Must measure and report latency vs. dataset size

**NFR-2: Index Build Time**

- Index building should be feasible for medium-sized collections
- Must measure and report build time vs. number of pages
- Progress indication required for long operations

**NFR-3: Concurrent Users**

- System should handle at least 10 concurrent users
- No significant performance degradation under load

### Scalability

**NFR-4: Dataset Growth**

- Indexing pipeline should support adding more books without code changes
- Database schema should accommodate growing data
- Index structure should scale sub-linearly

**NFR-5: Storage Efficiency**

- Index size should be monitored and optimized
- Compressed storage for large text fields where appropriate

### Reliability

**NFR-6: Error Handling**

- System handles invalid PDFs gracefully
- Empty queries rejected with clear error message
- Malformed requests return appropriate HTTP status codes
- Server errors logged and reported without exposing internals

**NFR-7: Data Integrity**

- No duplicate book uploads (filename uniqueness)
- No duplicate pages per book (bookId + pageNumber uniqueness)
- Atomic operations for critical workflows

### Security

**NFR-8: Authentication**

- JWT-based authentication
- Secure password hashing (bcrypt with salt rounds ≥10)
- Token expiration enforced

**NFR-9: Authorization**

- Role-based access control enforced
- Admin routes protected (401/403 responses)
- User data isolation (users can only see own history)

**NFR-10: Input Validation**

- All user inputs validated before processing
- File upload size limits enforced
- SQL/NoSQL injection prevention

**NFR-11: Rate Limiting**

- API rate limiting (120 requests/minute per IP)
- Prevents abuse and ensures fair usage

### Maintainability

**NFR-12: Code Quality**

- Clean modular codebase with separation of concerns
- Consistent naming conventions
- Self-documenting code structure
- No hardcoded credentials or secrets

**NFR-13: Documentation**

- API endpoints documented
- Code comments for complex algorithms
- README with setup instructions
- Architecture diagrams maintained

**NFR-14: Version Control**

- Professional Git workflow (branches, PRs, reviews)
- Meaningful commit messages (conventional commits)
- No direct commits to main branch

### Usability

**NFR-15: User Interface**

- Simple and intuitive UI
- Responsive design for different screen sizes
- Clear feedback for user actions
- Error messages are user-friendly

**NFR-16: Admin Interface**

- Clear upload progress indication
- Status messages for operations
- Confirmation for destructive actions

### Testability

**NFR-17: Unit Testing**

- Core modules (tokenizer, indexer, scorer) must be unit-testable
- Test coverage for critical business logic

**NFR-18: Integration Testing**

- End-to-end workflows testable
- API endpoints testable independently

**NFR-19: Evaluation Framework**

- Automated accuracy testing with test cases
- Metrics: Top-1/Top-5 accuracy, MRR
- Performance benchmarking scripts

### Deployment

**NFR-20: Environment Configuration**

- Configuration via environment variables
- No secrets in codebase
- Clear deployment documentation

**NFR-21: Cross-Platform**

- Works on Windows, Linux, macOS
- Database connection configurable (local/cloud)

---

## Constraints

1. Must use Node.js/Express for backend
2. Must use React for frontend
3. Must use MongoDB for database
4. Must NOT use AI/ML libraries for core search functionality
5. Must demonstrate professional GitHub workflow
6. Must complete within 6-month timeframe
7. Two-team member collaboration required
