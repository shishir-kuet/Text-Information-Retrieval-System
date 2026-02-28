import fitz  # PyMuPDF
from pymongo import MongoClient
from pathlib import Path
from datetime import datetime
import os
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

# -------- MONGODB CONNECTION --------
client = MongoClient('mongodb://localhost:27017/')
db = client['book_search_system']
books_collection = db['books']
pages_collection = db['pages']

# -------- CONFIGURATION --------
BOOKS_FOLDER = "books"
USE_OCR = True  # Set to False to skip scanned PDFs
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Update if different

# Try to set Tesseract path
try:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
except:
    USE_OCR = False

# -------- TEXT EXTRACTION FUNCTIONS --------
def extract_text_normal(page):
    """Extract text using PyMuPDF (for text-based PDFs)"""
    return str(page.get_text())

def extract_text_ocr(pdf_path, page_num):
    """Extract text using OCR (for scanned PDFs)"""
    try:
        # Convert PDF page to image
        images = convert_from_path(
            str(pdf_path),
            first_page=page_num + 1,
            last_page=page_num + 1,
            dpi=200
        )
        
        if images:
            # OCR the image
            text = pytesseract.image_to_string(images[0])
            return text
        return ""
    except Exception as e:
        print(f"       OCR Error: {str(e)}")
        return ""

def extract_page_text(doc, pdf_path, page_num):
    """Extract text from page, try normal first then OCR if needed"""
    page = doc[page_num]
    
    # Try normal extraction first
    text = extract_text_normal(page)
    
    # If empty or very short, try OCR
    if len(text.strip()) < 50 and USE_OCR:
        text = extract_text_ocr(pdf_path, page_num)
    
    return text

# -------- PROCESS ALL PDFs --------
def process_books():
    """
    Scan books folder, extract text from all PDFs,
    and store in MongoDB
    """
    
    # Clear existing data (optional - remove if you want to keep old data)
    print("Clearing existing data...")
    books_collection.delete_many({})
    pages_collection.delete_many({})
    print("✓ Database cleared\n")
    
    # Get all PDF files organized by domain
    books_path = Path(BOOKS_FOLDER)
    
    if not books_path.exists():
        print(f"Error: '{BOOKS_FOLDER}' folder not found!")
        return
    
    # Find all domain folders
    domain_folders = [f for f in books_path.iterdir() if f.is_dir()]
    
    if not domain_folders:
        print(f"No domain folders found in '{BOOKS_FOLDER}'!")
        print("Expected structure: books/history/, books/science/, etc.")
        return
    
    book_id = 1
    total_books = 0
    total_pages = 0
    
    print(f"{'='*70}")
    print(f" PROCESSING BOOKS")
    print(f"{'='*70}")
    if USE_OCR:
        print(f"✓ OCR enabled - will extract text from scanned PDFs")
    else:
        print(f"⚠️ OCR disabled - scanned PDFs will have empty text")
    print()
    
    # Process each domain folder
    for domain_folder in sorted(domain_folders):
        domain = domain_folder.name
        pdf_files = list(domain_folder.glob("*.pdf"))
        
        if not pdf_files:
            print(f"⚠ No PDFs found in {domain}/ folder\n")
            continue
        
        print(f"📁 Domain: {domain.upper()}")
        print(f"   Found {len(pdf_files)} book(s)\n")
        
        # Process each PDF in this domain
        for pdf_path in sorted(pdf_files):
            try:
                print(f"   📖 Processing: {pdf_path.name}")
                
                # Open PDF
                doc = fitz.open(str(pdf_path))
                num_pages = len(doc)
                
                # Extract book title from filename (remove .pdf extension)
                title = pdf_path.stem
                
                # Get file size
                file_size_mb = round(os.path.getsize(pdf_path) / (1024 * 1024), 2)
                
                # Store book metadata
                book_doc = {
                    "book_id": book_id,
                    "title": title,
                    "domain": domain,
                    "file_path": str(pdf_path),
                    "num_pages": num_pages,
                    "file_size_mb": file_size_mb,
                    "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                books_collection.insert_one(book_doc)
                
                # Extract and store pages
                pages_batch = []
                pages_with_text = 0
                pages_with_ocr = 0
                
                for page_num in range(num_pages):
                    text = extract_page_text(doc, pdf_path, page_num)
                    
                    # Track extraction success
                    if len(text.strip()) > 50:
                        if len(str(doc[page_num].get_text()).strip()) > 50:
                            pages_with_text += 1
                        else:
                            pages_with_ocr += 1
                    
                    page_doc = {
                        "page_id": f"{book_id}_{page_num + 1}",
                        "book_id": book_id,
                        "page_number": page_num + 1,
                        "text_content": text,
                        "word_count": len(text.split()),
                        "char_count": len(text)
                    }
                    
                    pages_batch.append(page_doc)
                    
                    # Show progress for large books
                    if (page_num + 1) % 100 == 0:
                        print(f"       Progress: {page_num + 1}/{num_pages} pages...")
                    
                    # Insert in batches of 100 pages for efficiency
                    if len(pages_batch) >= 100:
                        pages_collection.insert_many(pages_batch)
                        pages_batch = []
                
                # Insert remaining pages
                if pages_batch:
                    pages_collection.insert_many(pages_batch)
                
                doc.close()
                
                print(f"      ✓ Extracted {num_pages} pages ({file_size_mb} MB)")
                if pages_with_text > 0:
                    print(f"      ✓ Text-based pages: {pages_with_text}")
                if pages_with_ocr > 0:
                    print(f"      ✓ OCR pages: {pages_with_ocr}")
                if pages_with_text + pages_with_ocr == 0:
                    print(f"      ⚠️ Warning: No text extracted (scanned PDF, OCR not available)")
                print(f"      ✓ Stored in MongoDB with book_id: {book_id}\n")
                
                total_books += 1
                total_pages += num_pages
                book_id += 1
                
            except Exception as e:
                print(f"      ✗ Error: {str(e)}\n")
                continue
    
    # Final summary
    print(f"{'='*70}")
    print(f" PROCESSING COMPLETE")
    print(f"{'='*70}")
    print(f"Total Books Processed: {total_books}")
    print(f"Total Pages Extracted: {total_pages}")
    print(f"Database: book_search_system")
    print(f"Collections: books ({total_books} documents), pages ({total_pages} documents)")
    print(f"{'='*70}\n")
    
    # Show books summary
    print("📚 BOOKS SUMMARY:")
    print(f"{'ID':<5} {'Domain':<15} {'Title':<40} {'Pages':<8}")
    print(f"{'-'*70}")
    
    for book in books_collection.find().sort("book_id", 1):
        print(f"{book['book_id']:<5} {book['domain']:<15} {book['title'][:38]:<40} {book['num_pages']:<8}")

if __name__ == "__main__":
    process_books()
