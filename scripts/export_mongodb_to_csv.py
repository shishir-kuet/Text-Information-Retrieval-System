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

# -------- TEXT PREPROCESSING FUNCTIONS --------
def clean_text(text):
    """Clean text for model training - remove extra whitespace, special chars"""
    if not text:
        return ""
    
    # Remove multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    
    # Remove control characters but keep basic punctuation
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\x9F]', '', text)
    
    return text.strip()

def tokenize_simple(text):
    """Simple tokenization for word count"""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return len(text.split())

# -------- EXPORT FUNCTION 1: PAGES WITH METADATA (FOR TRAINING) --------
def export_pages_with_metadata(output_file="training_data.csv", limit=None):
    """
    Export pages with book metadata - ideal for text classification, 
    search ranking, or NLP model training
    """
    print(f"\n{'='*70}")
    print(f" EXPORTING PAGES WITH METADATA")
    print(f"{'='*70}")
    
    # Get all books first to create a lookup dictionary
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
    
    # Prepare output file
    output_path = Path(OUTPUT_DIR) / output_file
    
    print("Processing pages...")
    
    # Query pages with optional limit
    query = pages_collection.find()
    if limit:
        query = query.limit(limit)
    
    total_pages = pages_collection.count_documents({})
    pages_to_export = limit if limit else total_pages
    
    # Write to CSV with progress tracking
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
        for page in query:
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
            
            if count % 1000 == 0:
                print(f"   Progress: {count}/{pages_to_export} pages exported...")
    
    print(f"\n✓ Successfully exported {count} pages")
    print(f"✓ Output file: {output_path}")
    print(f"✓ File size: {output_path.stat().st_size / (1024*1024):.2f} MB\n")
    
    return output_path

# -------- EXPORT FUNCTION 2: BOOKS SUMMARY --------
def export_books_summary(output_file="books_metadata.csv"):
    """
    Export books metadata - useful for book-level analysis or filtering
    """
    print(f"\n{'='*70}")
    print(f" EXPORTING BOOKS METADATA")
    print(f"{'='*70}\n")
    
    books = list(books_collection.find())
    
    if not books:
        print("No books found in database!")
        return None
    
    # Convert to pandas DataFrame for easy export
    df = pd.DataFrame(books)
    
    # Drop MongoDB _id field
    if '_id' in df.columns:
        df = df.drop('_id', axis=1)
    
    # Reorder columns
    column_order = ['book_id', 'title', 'domain', 'num_pages', 
                   'file_size_mb', 'file_path', 'date_added']
    df = df[[col for col in column_order if col in df.columns]]
    
    output_path = Path(OUTPUT_DIR) / output_file
    df.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"✓ Successfully exported {len(df)} books")
    print(f"✓ Output file: {output_path}")
    print(f"✓ Columns: {', '.join(df.columns)}\n")
    
    return output_path

# -------- EXPORT FUNCTION 3: DOMAIN STATISTICS --------
def export_domain_statistics(output_file="domain_statistics.csv"):
    """
    Export statistics by domain - useful for understanding data distribution
    """
    print(f"\n{'='*70}")
    print(f" EXPORTING DOMAIN STATISTICS")
    print(f"{'='*70}\n")
    
    # Aggregate statistics by domain
    pipeline = [
        {
            '$lookup': {
                'from': 'pages',
                'localField': 'book_id',
                'foreignField': 'book_id',
                'as': 'pages'
            }
        },
        {
            '$group': {
                '_id': '$domain',
                'num_books': {'$sum': 1},
                'total_pages': {'$sum': '$num_pages'},
                'avg_pages_per_book': {'$avg': '$num_pages'},
                'total_file_size_mb': {'$sum': '$file_size_mb'},
                'total_words': {'$sum': {'$sum': '$pages.word_count'}}
            }
        },
        {
            '$sort': {'num_books': -1}
        }
    ]
    
    results = list(books_collection.aggregate(pipeline))
    
    if not results:
        print("No statistics to export!")
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    df = df.rename(columns={'_id': 'domain'})
    
    # Round numerical columns
    df['avg_pages_per_book'] = df['avg_pages_per_book'].round(1)
    df['total_file_size_mb'] = df['total_file_size_mb'].round(2)
    
    output_path = Path(OUTPUT_DIR) / output_file
    df.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"✓ Successfully exported statistics for {len(df)} domains")
    print(f"✓ Output file: {output_path}\n")
    
    # Print summary
    print("Domain Summary:")
    print(df.to_string(index=False))
    print()
    
    return output_path

# -------- EXPORT FUNCTION 4: CLEANED TEXT ONLY (FOR LANGUAGE MODELS) --------
def export_text_corpus(output_file="text_corpus.txt", min_words=50):
    """
    Export plain text corpus - ideal for language model pretraining
    Each line is one page's cleaned text
    """
    print(f"\n{'='*70}")
    print(f" EXPORTING TEXT CORPUS")
    print(f"{'='*70}\n")
    
    output_path = Path(OUTPUT_DIR) / output_file
    
    count = 0
    total_words = 0
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for page in pages_collection.find():
            text = clean_text(page.get('text_content', ''))
            word_count = len(text.split())
            
            # Only include pages with sufficient content
            if word_count >= min_words:
                f.write(text + '\n')
                count += 1
                total_words += word_count
                
                if count % 1000 == 0:
                    print(f"   Progress: {count} pages exported...")
    
    print(f"\n✓ Successfully exported {count} pages")
    print(f"✓ Total words: {total_words:,}")
    print(f"✓ Average words per page: {total_words/count:.1f}")
    print(f"✓ Output file: {output_path}")
    print(f"✓ File size: {output_path.stat().st_size / (1024*1024):.2f} MB\n")
    
    return output_path

# -------- EXPORT FUNCTION 5: STRATIFIED SAMPLE FOR TRAINING/VALIDATION --------
def export_stratified_sample(train_ratio=0.8, output_prefix="stratified"):
    """
    Export training and validation sets with stratified sampling by domain
    Ensures balanced representation of each domain in both sets
    """
    print(f"\n{'='*70}")
    print(f" EXPORTING STRATIFIED TRAIN/VAL SPLIT")
    print(f"{'='*70}\n")
    
    # Get all pages with domain info
    pipeline = [
        {
            '$lookup': {
                'from': 'books',
                'localField': 'book_id',
                'foreignField': 'book_id',
                'as': 'book_info'
            }
        },
        {
            '$unwind': '$book_info'
        },
        {
            '$project': {
                'page_id': 1,
                'book_id': 1,
                'page_number': 1,
                'text_content': 1,
                'word_count': 1,
                'domain': '$book_info.domain',
                'book_title': '$book_info.title'
            }
        }
    ]
    
    print("Loading all pages with metadata...")
    pages_data = list(pages_collection.aggregate(pipeline))
    
    if not pages_data:
        print("No data found!")
        return None
    
    df = pd.DataFrame(pages_data)
    df = df.drop('_id', axis=1)
    
    print(f"✓ Loaded {len(df)} pages\n")
    
    # Stratified split by domain
    train_dfs = []
    val_dfs = []
    
    print("Splitting by domain:")
    for domain in df['domain'].unique():
        domain_df = df[df['domain'] == domain]
        n_train = int(len(domain_df) * train_ratio)
        
        # Shuffle and split
        domain_df = domain_df.sample(frac=1, random_state=42).reset_index(drop=True)
        train_dfs.append(domain_df[:n_train])
        val_dfs.append(domain_df[n_train:])
        
        print(f"   {domain}: {n_train} train, {len(domain_df)-n_train} validation")
    
    train_df = pd.concat(train_dfs, ignore_index=True)
    val_df = pd.concat(val_dfs, ignore_index=True)
    
    # Shuffle again
    train_df = train_df.sample(frac=1, random_state=42).reset_index(drop=True)
    val_df = val_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Add cleaned text
    train_df['cleaned_text'] = train_df['text_content'].apply(clean_text)
    val_df['cleaned_text'] = val_df['text_content'].apply(clean_text)
    
    # Export
    train_path = Path(OUTPUT_DIR) / f"{output_prefix}_train.csv"
    val_path = Path(OUTPUT_DIR) / f"{output_prefix}_val.csv"
    
    train_df.to_csv(train_path, index=False, encoding='utf-8')
    val_df.to_csv(val_path, index=False, encoding='utf-8')
    
    print(f"\n✓ Training set: {len(train_df)} pages → {train_path}")
    print(f"✓ Validation set: {len(val_df)} pages → {val_path}")
    print(f"✓ Split ratio: {train_ratio:.0%} train / {1-train_ratio:.0%} validation\n")
    
    return train_path, val_path

# -------- MAIN MENU --------
def main():
    """Interactive menu for exporting data"""
    print(f"\n{'='*70}")
    print(f" MONGODB TO CSV EXPORT TOOL")
    print(f" Database: book_search_system")
    print(f"{'='*70}")
    
    # Show database stats
    num_books = books_collection.count_documents({})
    num_pages = pages_collection.count_documents({})
    
    print(f"\nCurrent Database Status:")
    print(f"   Books: {num_books}")
    print(f"   Pages: {num_pages}")
    print(f"   Export Directory: {OUTPUT_DIR}\n")
    
    if num_books == 0 or num_pages == 0:
        print("⚠️  No data found in database. Please run process_books_to_mongodb.py first!")
        return
    
    print("Choose export option:")
    print("\n1. Pages with Metadata (Complete training dataset)")
    print("   → Best for: Text classification, search ranking, NLP models")
    print("   → Includes: page text, book info, domain labels")
    
    print("\n2. Books Metadata Only")
    print("   → Best for: Book-level analysis, cataloging")
    print("   → Includes: book info, statistics")
    
    print("\n3. Domain Statistics")
    print("   → Best for: Understanding data distribution")
    print("   → Includes: aggregated stats per domain")
    
    print("\n4. Text Corpus (Plain text)")
    print("   → Best for: Language model pretraining")
    print("   → Includes: cleaned text only, one page per line")
    
    print("\n5. Stratified Train/Val Split")
    print("   → Best for: Model training with balanced datasets")
    print("   → Includes: 80/20 split stratified by domain")
    
    print("\n6. Export All")
    print("   → Generates all export formats")
    
    print("\n0. Exit")
    
    choice = input("\nEnter your choice (0-6): ").strip()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if choice == "1":
        export_pages_with_metadata(f"training_data_{timestamp}.csv")
    
    elif choice == "2":
        export_books_summary(f"books_metadata_{timestamp}.csv")
    
    elif choice == "3":
        export_domain_statistics(f"domain_statistics_{timestamp}.csv")
    
    elif choice == "4":
        export_text_corpus(f"text_corpus_{timestamp}.txt")
    
    elif choice == "5":
        export_stratified_sample(output_prefix=f"stratified_{timestamp}")
    
    elif choice == "6":
        print("\nExporting all formats...\n")
        export_pages_with_metadata(f"training_data_{timestamp}.csv")
        export_books_summary(f"books_metadata_{timestamp}.csv")
        export_domain_statistics(f"domain_statistics_{timestamp}.csv")
        export_text_corpus(f"text_corpus_{timestamp}.txt")
        export_stratified_sample(output_prefix=f"stratified_{timestamp}")
        print("\n✅ All exports completed!")
    
    elif choice == "0":
        print("\nExiting...")
        return
    
    else:
        print("\n❌ Invalid choice!")
        return
    
    print(f"\n{'='*70}")
    print(f" EXPORT COMPLETED")
    print(f"{'='*70}")
    print(f"All files saved to: {OUTPUT_DIR}\n")

if __name__ == "__main__":
    main()
