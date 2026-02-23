# System Scope

## In Scope

The system operates on a controlled digital library (initially 30 books). It supports admin ingestion of books, indexing of extracted pages, and user search over the indexed content.

### Features Included

1. **Book Management**
   - Admin uploads PDF books with metadata
   - Store books and page-wise text in database
   - View and manage book collection

2. **Text Extraction (OCR)**
   - OCR processing for scanned PDF images
   - Page-by-page text extraction using Tesseract OCR
   - Image preprocessing for better OCR accuracy
   - Handle multi-page PDF documents
   - Error handling for unreadable pages

3. **Indexing System**
   - Build inverted index over pages
   - Tokenization and normalization
   - Stopword removal
   - Term frequency calculation
   - Document frequency tracking

4. **Search & Ranking**
   - Process user queries (normalize, tokenize)
   - Rank results using TF-IDF algorithm
   - Return top-K results with book metadata and page number
   - Generate snippets with context

5. **User Features**
   - Text-based search interface
   - View search results with scores
   - Page preview with highlighted terms
   - Search history

6. **Admin Features**
   - PDF upload and processing
   - Index build/rebuild
   - View search logs and analytics

7. **Security**
   - Authentication (registration/login)
   - Role-based access control (Admin/User)
   - Protected admin routes

8. **Analysis & Testing**
   - Performance measurement (index time, search time, index size)
   - Evaluation scripts for accuracy testing
   - Unit and integration tests

## Out of Scope

1. Searching the whole internet or external web pages
2. Copyright-violating distribution of full book PDFs to public
3. Real-time collaborative features
4. Mobile application development
5. Advanced NLP features (summarization, translation, etc.)
6. Handwritten text recognition (only printed text via OCR)

## Assumptions

1. Books are available as scanned PDF images (requiring OCR processing)
2. PDFs contain printed text (not handwritten)
3. Admin has permission to store and process the book texts for academic purposes
4. Dataset is in English language
5. Books have reasonable scan quality (readable by OCR)
6. Users have basic computer literacy
7. System will be deployed on local/university network (not public internet initially)
8. Tesseract OCR or equivalent is available on server

## Limitations

1. **OCR Accuracy**: OCR may introduce errors for poor quality scans, unusual fonts, or low-resolution images
2. **OCR Processing Time**: Text extraction via OCR is slower than parsing machine-readable PDFs
3. **Lexical Matching**: TF-IDF handles lexical similarity; paraphrased or semantically similar text may not match well
4. **Page Boundary Detection**: PDF page extraction relies on PDF structure
5. **Language**: Currently supports English only
6. **Scale**: Optimized for medium-sized collections (100-1000 books)
7. **Real-time Updates**: Index must be rebuilt after adding new books (not incremental)
8. **Special Characters**: Mathematical symbols, tables, or complex layouts may not OCR accurately

## Future Enhancements (Out of Current Scope)

- Incremental index updates
- Multi-language support
- Semantic search capabilities
- Book recommendation system
- Citation detection and linking
- Export/download features
- Advanced analytics dashboard
