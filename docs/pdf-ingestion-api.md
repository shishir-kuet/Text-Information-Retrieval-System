# PDF Ingestion API Documentation

This module handles PDF file uploads, OCR processing, and text extraction for the Text Information Retrieval System.

## Architecture

```
PDF Upload → Multer Storage → PDF Service → OCR Service → Database
                                    ↓
                              Page-by-Page Processing
                                    ↓
                         Store in Book & Page Collections
```

## API Endpoints

### 1. Upload PDF Book

**Endpoint:** `POST /api/books/upload`

**Description:** Upload a PDF file and process it with OCR to extract text from all pages.

**Request:**

- **Content-Type:** `multipart/form-data`
- **Body Parameters:**
  - `pdf` (file, required): PDF file to upload (max 50MB)
  - `title` (string, optional): Book title (defaults to filename)
  - `author` (string, optional): Author name (defaults to "Unknown")
  - `year` (number, optional): Publication year
  - `source` (string, optional): Source or collection name

**Example using cURL:**

```bash
curl -X POST http://localhost:5000/api/books/upload \
  -F "pdf=@/path/to/book.pdf" \
  -F "title=Sample Book" \
  -F "author=John Doe" \
  -F "year=2024" \
  -F "source=Digital Library"
```

**Example using Postman:**

1. Select `POST` method
2. Enter URL: `http://localhost:5000/api/books/upload`
3. Go to `Body` tab → Select `form-data`
4. Add fields:
   - Key: `pdf`, Type: `File`, Value: Select your PDF
   - Key: `title`, Type: `Text`, Value: "Your Book Title"
   - Key: `author`, Type: `Text`, Value: "Author Name"
   - Key: `year`, Type: `Text`, Value: "2024"
   - Key: `source`, Type: `Text`, Value: "Source Name"
5. Click `Send`

**Response (201 Created):**

```json
{
  "success": true,
  "message": "Book uploaded and processed successfully",
  "data": {
    "bookId": "65f1a2b3c4d5e6f7a8b9c0d1",
    "title": "Sample Book",
    "author": "John Doe",
    "totalPages": 150,
    "status": "processed"
  }
}
```

**Error Response (400 Bad Request):**

```json
{
  "success": false,
  "message": "No PDF file uploaded"
}
```

---

### 2. Get All Books

**Endpoint:** `GET /api/books`

**Description:** Retrieve a list of all uploaded books.

**Response (200 OK):**

```json
{
  "success": true,
  "count": 3,
  "data": [
    {
      "_id": "65f1a2b3c4d5e6f7a8b9c0d1",
      "title": "Sample Book 1",
      "author": "John Doe",
      "year": 2024,
      "fileName": "1234567890-sample.pdf",
      "totalPages": 150,
      "status": "processed",
      "ocrCompleted": true,
      "createdAt": "2024-03-15T10:30:00.000Z",
      "updatedAt": "2024-03-15T10:35:00.000Z"
    }
  ]
}
```

---

### 3. Get Book by ID

**Endpoint:** `GET /api/books/:id`

**Description:** Retrieve a specific book with all its pages.

**URL Parameters:**

- `id` (string, required): Book MongoDB ObjectId

**Example:**

```bash
curl http://localhost:5000/api/books/65f1a2b3c4d5e6f7a8b9c0d1
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "book": {
      "_id": "65f1a2b3c4d5e6f7a8b9c0d1",
      "title": "Sample Book",
      "author": "John Doe",
      "totalPages": 150,
      "status": "processed"
    },
    "pages": [
      {
        "_id": "65f1a2b3c4d5e6f7a8b9c0d2",
        "bookId": "65f1a2b3c4d5e6f7a8b9c0d1",
        "pageNumber": 1,
        "text": "This is the extracted text from page 1...",
        "tokenCount": 245,
        "ocrConfidence": 95.5
      }
    ],
    "pageCount": 150
  }
}
```

**Error Response (404 Not Found):**

```json
{
  "success": false,
  "message": "Book not found"
}
```

---

### 4. Get Book Processing Status

**Endpoint:** `GET /api/books/:id/status`

**Description:** Check the processing status of a book.

**URL Parameters:**

- `id` (string, required): Book MongoDB ObjectId

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "title": "Sample Book",
    "status": "processing",
    "totalPages": 150,
    "ocrCompleted": false,
    "ocrError": null
  }
}
```

**Status Values:**

- `uploaded`: PDF uploaded, not yet processed
- `processing`: OCR in progress
- `processed`: Successfully processed
- `indexed`: Inverted index created (from Step 5)
- `failed`: Processing failed (check `ocrError`)

---

### 5. Delete Book

**Endpoint:** `DELETE /api/books/:id`

**Description:** Delete a book and all its pages. Also removes the PDF file from storage.

**URL Parameters:**

- `id` (string, required): Book MongoDB ObjectId

**Example:**

```bash
curl -X DELETE http://localhost:5000/api/books/65f1a2b3c4d5e6f7a8b9c0d1
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Book deleted successfully"
}
```

**Error Response (404 Not Found):**

```json
{
  "success": false,
  "message": "Book not found"
}
```

---

## File Upload Configuration

**Multer Settings:**

- **Storage:** Disk storage in `backend/uploads/` directory
- **File Naming:** `timestamp-random-originalname.pdf`
- **File Filter:** Only PDF files allowed (`application/pdf`)
- **Size Limit:** 50MB maximum
- **Single Upload:** One file per request (field name: `pdf`)

---

## OCR Processing

### Technology Stack:

- **Tesseract.js**: Open-source OCR engine
- **Language:** English (eng) trained data
- **Processing Time:** ~2-5 seconds per page (depends on image quality and page complexity)

### Processing Pipeline:

1. **PDF Upload**: File saved to disk via Multer
2. **Book Record Creation**: Entry created in database with `status: "processing"`
3. **Page Count Detection**: Total pages extracted from PDF metadata
4. **Page-by-Page Processing**:
   - Extract page content
   - For machine-readable PDFs: Direct text extraction
   - For scanned PDFs: OCR text extraction (Tesseract)
   - Calculate token count
   - Store confidence score
   - Save to `Page` collection
5. **Completion**: Update book `status: "processed"` and `ocrCompleted: true`
6. **Error Handling**: If processing fails, set `status: "failed"` and store error in `ocrError`

### OCR Confidence Scores:

- **100**: Direct text extraction (machine-readable PDF)
- **85-98**: High-quality scanned pages
- **70-84**: Medium-quality scans
- **<70**: Low-quality scans (may need review)
- **0**: OCR not attempted or failed

---

## Database Models Used

### Book Model:

```javascript
{
  title: String,
  author: String,
  year: Number,
  source: String,
  fileName: String (unique),
  totalPages: Number,
  status: Enum ["uploaded", "processing", "processed", "indexed", "failed"],
  ocrCompleted: Boolean,
  ocrError: String
}
```

### Page Model:

```javascript
{
  bookId: ObjectId (ref: Book),
  pageNumber: Number,
  text: String,
  tokenCount: Number,
  ocrConfidence: Number (0-100)
}
```

---

## Error Handling

### Common Errors:

**1. File Not Uploaded**

```json
{
  "success": false,
  "message": "No PDF file uploaded"
}
```

**2. Invalid File Type**

```json
{
  "success": false,
  "message": "Only PDF files are allowed!"
}
```

**3. File Too Large**

```json
{
  "success": false,
  "message": "File too large. Maximum size is 50MB"
}
```

**4. OCR Processing Failed**

- Book status set to `"failed"`
- Error details stored in `ocrError` field
- Check book status endpoint for details

---

## Testing

### Run Verification Script:

```bash
npm run check:pdf
```

This checks:

- Multer configuration loaded
- OCR and PDF services loaded
- Book controller methods present
- Book routes registered
- Required dependencies installed
- Uploads directory exists

### Manual Testing with Sample PDF:

1. **Start the server:**

   ```bash
   npm run dev
   ```

2. **Upload a PDF:**

   ```bash
   curl -X POST http://localhost:5000/api/books/upload \
     -F "pdf=@sample.pdf" \
     -F "title=Test Book" \
     -F "author=Test Author"
   ```

3. **Check processing status:**

   ```bash
   curl http://localhost:5000/api/books/{bookId}/status
   ```

4. **Get all books:**

   ```bash
   curl http://localhost:5000/api/books
   ```

5. **Get book with pages:**
   ```bash
   curl http://localhost:5000/api/books/{bookId}
   ```

---

## Performance Considerations

### Expected Processing Times:

- **Upload**: < 1 second (depends on file size and network)
- **OCR per page**: 2-5 seconds
- **Total for 100-page book**: 3-8 minutes
- **Total for 30 books (~3000 pages)**: 8-10 hours

### Optimization Recommendations:

1. **Parallel Processing**: Process multiple pages concurrently (future enhancement)
2. **Queue System**: Use job queue (Bull, BeeQueue) for background processing
3. **Progress Tracking**: Implement WebSocket for real-time progress updates
4. **Caching**: Cache OCR worker initialization
5. **Image Preprocessing**: Enhance image quality before OCR (deskew, denoise, threshold)

---

## Future Enhancements

- [ ] Background job processing with queue system
- [ ] Real-time progress updates via WebSockets
- [ ] Batch upload multiple PDFs
- [ ] PDF page-to-image conversion for true scanned PDF support
- [ ] Image preprocessing for better OCR accuracy
- [ ] Support for multiple languages
- [ ] Automatic language detection
- [ ] OCR quality metrics and validation
- [ ] Resume failed processing
- [ ] Authentication and authorization for admin endpoints
