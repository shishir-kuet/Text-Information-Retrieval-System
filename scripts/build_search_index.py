from pymongo import MongoClient
import re
import pickle
from collections import defaultdict, Counter
from datetime import datetime

# -------- MONGODB CONNECTION --------
client = MongoClient('mongodb://localhost:27017/')
db = client['book_search_system']
books_collection = db['books']
pages_collection = db['pages']

# -------- CONFIGURATION --------
INDEX_FILE = "data/search_index.pkl"

# -------- TEXT PREPROCESSING --------
def tokenize(text):
    """Convert text to lowercase and extract words"""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return text.split()

# -------- BUILD SEARCH INDEX --------
def build_index():
    """
    Build BM25 inverted index from MongoDB pages collection
    """
    
    print(f"{'='*70}")
    print(f" BUILDING SEARCH INDEX")
    print(f"{'='*70}\n")
    
    # Get counts
    total_books = books_collection.count_documents({})
    total_pages = pages_collection.count_documents({})
    
    print(f"Books in database: {total_books}")
    print(f"Pages in database: {total_pages}")
    print(f"\nProcessing pages...\n")
    
    if total_pages == 0:
        print("Error: No pages found in database!")
        print("Run 'process_books_to_mongodb.py' first.")
        return
    
    # Data structures for BM25
    inverted_index = defaultdict(list)   # term → [(book_id, page_no), ...]
    term_freqs = {}                      # (book_id, page_no) → Counter(term)
    doc_lengths = {}                     # (book_id, page_no) → length
    
    # Fetch all pages from MongoDB
    pages_processed = 0
    empty_pages = 0
    
    for page_doc in pages_collection.find():
        book_id = page_doc['book_id']
        page_number = page_doc['page_number']
        text = page_doc['text_content']
        
        doc_id = (book_id, page_number)
        
        # Skip empty pages
        if not text or len(text.strip()) == 0:
            empty_pages += 1
            continue
        
        # Tokenize and build term frequencies
        tokens = tokenize(text)
        freq = Counter(tokens)
        
        term_freqs[doc_id] = freq
        doc_lengths[doc_id] = sum(freq.values())
        
        # Build inverted index
        for term in freq:
            inverted_index[term].append(doc_id)
        
        pages_processed += 1
        
        # Progress indicator
        if pages_processed % 1000 == 0:
            print(f"   Processed {pages_processed}/{total_pages} pages...")
    
    N = pages_processed  # Total documents
    
    print(f"\n{'='*70}")
    print(f" INDEX BUILT SUCCESSFULLY")
    print(f"{'='*70}")
    print(f"Total pages indexed: {N}")
    print(f"Empty pages skipped: {empty_pages}")
    print(f"Unique terms: {len(inverted_index)}")
    print(f"Average document length: {round(sum(doc_lengths.values()) / N, 2)} terms")
    print(f"{'='*70}\n")
    
    # Load books metadata for search results
    books_metadata = {}
    for book in books_collection.find():
        books_metadata[book['book_id']] = {
            'title': book['title'],
            'domain': book['domain'],
            'num_pages': book['num_pages']
        }
    
    # Save index to pickle file
    index_data = {
        "books_metadata": books_metadata,
        "inverted_index": dict(inverted_index),
        "term_freqs": term_freqs,
        "doc_lengths": doc_lengths,
        "N": N,
        "build_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Create data folder if it doesn't exist
    import os
    os.makedirs("data", exist_ok=True)
    
    with open(INDEX_FILE, "wb") as f:
        pickle.dump(index_data, f)
    
    print(f"Index saved to: {INDEX_FILE}")
    
    # Show index statistics
    print(f"\n--- INDEX STATISTICS ---")
    print(f"Index file size: {round(os.path.getsize(INDEX_FILE) / (1024*1024), 2)} MB")
    
    # Show domain distribution
    domain_stats = defaultdict(int)
    for book_id, meta in books_metadata.items():
        domain_stats[meta['domain']] += 1
    
    print(f"\nBooks by domain:")
    for domain, count in sorted(domain_stats.items()):
        print(f"  {domain}: {count} book(s)")
    
    # Show some sample terms
    sample_terms = sorted(inverted_index.keys())[:10]
    print(f"\nSample indexed terms: {', '.join(sample_terms)}")

if __name__ == "__main__":
    build_index()
