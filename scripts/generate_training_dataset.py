from pymongo import MongoClient
import re
import json
import random
from collections import Counter
from datetime import datetime

# -------- MONGODB CONNECTION --------
client = MongoClient('mongodb://localhost:27017/')
db = client['book_search_system']
pages_collection = db['pages']

# -------- CONFIGURATION --------
QUERIES_PER_PAGE = 3  # Generate 3-5 queries per page (we'll randomize)
CANDIDATES_PER_QUERY = 10  # Number of candidate pages per query
MIN_WORD_COUNT = 50  # Skip pages with too few words
OUTPUT_FILE = "training_dataset.json"

print("=" * 60)
print("TRAINING DATASET GENERATOR")
print("=" * 60)

# -------- TEXT PREPROCESSING --------
def tokenize(text):
    """Convert text to lowercase and extract words"""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = text.split()
    return [t for t in tokens if len(t) > 2]  # Remove very short words

def remove_stopwords(tokens):
    """Remove common English stopwords"""
    stopwords = {
        'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are', 'was', 'were',
        'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
        'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'who', 'when',
        'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most',
        'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
        'than', 'too', 'very', 'and', 'but', 'or', 'if', 'then', 'for', 'with',
        'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'to', 'from', 'up', 'down', 'in', 'out', 'of', 'by'
    }
    return [t for t in tokens if t not in stopwords]

def extract_ngrams(tokens, n=2):
    """Extract n-grams from tokens"""
    ngrams = []
    for i in range(len(tokens) - n + 1):
        ngrams.append(' '.join(tokens[i:i+n]))
    return ngrams

# -------- QUERY GENERATION --------
def generate_queries_from_page(text_content, num_queries=3):
    """Generate queries from page text using keyword extraction"""
    queries = []
    
    # Tokenize and remove stopwords
    tokens = tokenize(text_content)
    filtered_tokens = remove_stopwords(tokens)
    
    if len(filtered_tokens) < 10:
        return []
    
    # Get most frequent terms (unigrams)
    term_freq = Counter(filtered_tokens)
    top_unigrams = [word for word, _ in term_freq.most_common(15)]
    
    # Get bigrams (phrases)
    bigrams = extract_ngrams(filtered_tokens, 2)
    bigram_freq = Counter(bigrams)
    top_bigrams = [phrase for phrase, _ in bigram_freq.most_common(10)]
    
    # Get trigrams (longer phrases)
    trigrams = extract_ngrams(filtered_tokens, 3)
    trigram_freq = Counter(trigrams)
    top_trigrams = [phrase for phrase, _ in trigram_freq.most_common(5)]
    
    # Generate queries by mixing unigrams, bigrams, and trigrams
    for _ in range(num_queries):
        query_type = random.choice(['unigram', 'bigram', 'trigram', 'mixed'])
        query = ""
        
        if query_type == 'unigram' and len(top_unigrams) >= 2:
            # Pick 2-4 top unigrams
            max_terms = min(4, len(top_unigrams))
            num_terms = random.randint(2, max_terms)
            query = ' '.join(random.sample(top_unigrams, num_terms))
            
        elif query_type == 'bigram' and top_bigrams:
            # Use a bigram
            query = random.choice(top_bigrams)
            
        elif query_type == 'trigram' and top_trigrams:
            # Use a trigram
            query = random.choice(top_trigrams)
            
        elif len(top_unigrams) >= 2 or top_bigrams:  # mixed - fallback
            # Combine a bigram with a unigram, or just use what's available
            parts = []
            if top_bigrams:
                parts.append(random.choice(top_bigrams))
            if len(top_unigrams) >= 1:
                parts.append(random.choice(top_unigrams))
            query = ' '.join(parts)
        
        if query and len(query.split()) >= 2:  # Ensure query has at least 2 words
            queries.append(query)
    
    return list(set(queries))  # Remove duplicates

# -------- SCORING FUNCTIONS --------
def calculate_word_overlap(query, page_text):
    """Calculate how many query words appear in the page"""
    query_tokens = set(tokenize(query))
    page_tokens = set(tokenize(page_text))
    overlap = query_tokens.intersection(page_tokens)
    return len(overlap)

def has_query_word_overlap(query, page_text, min_overlap=1):
    """Check if page has at least min_overlap words from query"""
    return calculate_word_overlap(query, page_text) >= min_overlap

# -------- DATASET GENERATION --------
def generate_training_dataset():
    """Main function to generate the training dataset"""
    
    # Fetch all pages from MongoDB
    print("\nFetching pages from MongoDB...")
    all_pages = list(pages_collection.find())
    print(f"Total pages found: {len(all_pages)}")
    
    if len(all_pages) == 0:
        print("ERROR: No pages found in the database!")
        return
    
    # Filter pages by word count
    valid_pages = [p for p in all_pages if p.get('word_count', 0) >= MIN_WORD_COUNT]
    print(f"Pages with sufficient word count: {len(valid_pages)}")
    
    if len(valid_pages) == 0:
        print("ERROR: No valid pages found!")
        return
    
    # Group pages by book_id
    pages_by_book = {}
    for page in valid_pages:
        book_id = page.get('book_id')
        if book_id not in pages_by_book:
            pages_by_book[book_id] = []
        pages_by_book[book_id].append(page)
    
    print(f"Books represented: {len(pages_by_book)}")
    
    # Generate training data
    training_data = []
    total_queries = 0
    
    print("\nGenerating queries and training samples...")
    
    for idx, source_page in enumerate(valid_pages, 1):
        if idx % 10 == 0:
            print(f"  Processed {idx}/{len(valid_pages)} pages...")
        
        text_content = source_page.get('text_content', '')
        book_id = source_page.get('book_id')
        page_number = source_page.get('page_number')
        page_id = str(source_page.get('_id'))
        
        # Generate queries from this page
        num_queries = random.randint(3, 5)
        queries = generate_queries_from_page(text_content, num_queries)
        
        if not queries:
            continue
        
        total_queries += len(queries)
        
        # For each generated query, create training samples
        for query in queries:
            candidates = []
            
            # 1. Add the source page with label 2
            candidates.append({
                "query": query,
                "page_id": page_id,
                "book_id": book_id,
                "page_number": page_number,
                "word_overlap_score": calculate_word_overlap(query, text_content),
                "relevance_label": 2,
                "page_text_snippet": text_content[:200].strip()
            })
            
            # 2. Add other pages from the same book with some overlap (label 1)
            same_book_pages = [p for p in pages_by_book.get(book_id, []) 
                             if str(p.get('_id')) != page_id]
            
            if same_book_pages:
                # Find pages with word overlap
                overlap_pages = []
                for p in same_book_pages:
                    if has_query_word_overlap(query, p.get('text_content', ''), min_overlap=1):
                        overlap_pages.append(p)
                
                # Add up to 4 pages with overlap
                num_overlap = min(4, len(overlap_pages))
                selected_overlap = random.sample(overlap_pages, num_overlap) if overlap_pages else []
                
                for p in selected_overlap:
                    candidates.append({
                        "query": query,
                        "page_id": str(p.get('_id')),
                        "book_id": p.get('book_id'),
                        "page_number": p.get('page_number'),
                        "word_overlap_score": calculate_word_overlap(query, p.get('text_content', '')),
                        "relevance_label": 1,
                        "page_text_snippet": p.get('text_content', '')[:200].strip()
                    })
            
            # 3. Add unrelated pages from other books (label 0)
            other_books_pages = [p for p in valid_pages if p.get('book_id') != book_id]
            
            if other_books_pages:
                num_unrelated = CANDIDATES_PER_QUERY - len(candidates)
                num_unrelated = max(0, min(num_unrelated, len(other_books_pages)))
                
                selected_unrelated = random.sample(other_books_pages, num_unrelated)
                
                for p in selected_unrelated:
                    candidates.append({
                        "query": query,
                        "page_id": str(p.get('_id')),
                        "book_id": p.get('book_id'),
                        "page_number": p.get('page_number'),
                        "word_overlap_score": calculate_word_overlap(query, p.get('text_content', '')),
                        "relevance_label": 0,
                        "page_text_snippet": p.get('text_content', '')[:200].strip()
                    })
            
            # Add all candidates for this query to training data
            training_data.extend(candidates)
    
    print(f"\nDataset generation complete!")
    print(f"Total queries generated: {total_queries}")
    print(f"Total training samples: {len(training_data)}")
    
    # Save to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"training_dataset_{timestamp}.json"
    output_path = f"data/{output_filename}"
    
    print(f"\nSaving dataset to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(training_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Dataset saved successfully!")
    
    # Print statistics
    print("\n" + "=" * 60)
    print("DATASET STATISTICS")
    print("=" * 60)
    
    label_counts = Counter(sample['relevance_label'] for sample in training_data)
    print(f"Samples with label 0 (unrelated): {label_counts[0]}")
    print(f"Samples with label 1 (same book, some overlap): {label_counts[1]}")
    print(f"Samples with label 2 (source page): {label_counts[2]}")
    
    avg_overlap = sum(sample['word_overlap_score'] for sample in training_data) / len(training_data)
    print(f"Average word overlap score: {avg_overlap:.2f}")
    
    print("\n" + "=" * 60)
    print("Sample entries:")
    print("=" * 60)
    for i, sample in enumerate(training_data[:3]):
        print(f"\nSample {i+1}:")
        print(f"  Query: {sample['query']}")
        print(f"  Book ID: {sample['book_id']}, Page: {sample['page_number']}")
        print(f"  Overlap Score: {sample['word_overlap_score']}")
        print(f"  Relevance Label: {sample['relevance_label']}")
        print(f"  Snippet: {sample['page_text_snippet'][:80]}...")

# -------- MAIN EXECUTION --------
if __name__ == "__main__":
    try:
        generate_training_dataset()
        print("\n✓ Process completed successfully!")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
