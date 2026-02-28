import pandas as pd
from pymongo import MongoClient
import csv
from pathlib import Path
import re
from datetime import datetime

# -------- MONGODB CONNECTION --------
client = MongoClient('mongodb://localhost:27017/')
db = client['book_search_system']
books_collection = db['books']
pages_collection = db['pages']

# -------- CONFIGURATION --------
OUTPUT_DIR = "data/exports"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# -------- TEXT PREPROCESSING --------
def clean_text(text):
    """Clean text for model training"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\x9F]', '', text)
    return text.strip()

def tokenize_simple(text):
    """Simple tokenization for word count"""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return len(text.split())

# -------- EXPORT --------
print(f"\n{'='*70}")
print(f" EXPORTING MONGODB DATA TO CSV")
print(f"{'='*70}\n")

# Check database
num_books = books_collection.count_documents({})
num_pages = pages_collection.count_documents({})

print(f"Database Status:")
print(f"   Books: {num_books}")
print(f"   Pages: {num_pages}\n")

if num_books == 0 or num_pages == 0:
    print("⚠️  No data found in database!")
    exit(1)

# Get books metadata
print("Loading books metadata...")
books_dict = {}
for book in books_collection.find():
    books_dict[book['book_id']] = {
        'title': book.get('title', ''),
        'domain': book.get('domain', ''),
        'num_pages': book.get('num_pages', 0),
        'file_size_mb': book.get('file_size_mb', 0.0)
    }

print(f"✓ Loaded {len(books_dict)} books\n")

# Export pages with metadata
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"training_data_{timestamp}.csv"
output_path = Path(OUTPUT_DIR) / output_file

print(f"Exporting to: {output_path}")
print("Processing pages...\n")

with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = [
        'page_id',
        'book_id',
        'page_number',
        'book_title',
        'domain',
        'text_content',
        'cleaned_text',
        'word_count',
        'char_count',
        'token_count'
    ]
    
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    
    count = 0
    for page in pages_collection.find():
        book_id = page['book_id']
        book_info = books_dict.get(book_id, {})
        
        text_content = page.get('text_content', '')
        cleaned = clean_text(text_content)
        
        row = {
            'page_id': page.get('page_id', ''),
            'book_id': book_id,
            'page_number': page.get('page_number', 0),
            'book_title': book_info.get('title', ''),
            'domain': book_info.get('domain', ''),
            'text_content': text_content,
            'cleaned_text': cleaned,
            'word_count': page.get('word_count', 0),
            'char_count': page.get('char_count', 0),
            'token_count': tokenize_simple(cleaned)
        }
        
        writer.writerow(row)
        count += 1
        
        if count % 100 == 0:
            print(f"   Progress: {count}/{num_pages} pages exported...")

print(f"\n{'='*70}")
print(f" EXPORT COMPLETED")
print(f"{'='*70}")
print(f"✓ Successfully exported {count} pages")
print(f"✓ Output file: {output_path}")
print(f"✓ File size: {output_path.stat().st_size / (1024*1024):.2f} MB")
print(f"\nColumns in CSV:")
for field in fieldnames:
    print(f"   - {field}")
print()
