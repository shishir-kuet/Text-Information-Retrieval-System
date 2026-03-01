from pymongo import MongoClient
import pickle
import re
import math
from collections import Counter

# -------- MONGODB CONNECTION --------
client = MongoClient('mongodb://localhost:27017/')
db = client['book_search_system']
pages_collection = db['pages']

# -------- LOAD INDEX --------
INDEX_FILE = "data/search_index.pkl"

print(f"Loading search index from {INDEX_FILE}...")
with open(INDEX_FILE, "rb") as f:
    data = pickle.load(f)

books_metadata = data["books_metadata"]
inverted_index = data["inverted_index"]
term_freqs = data["term_freqs"]
doc_lengths = data["doc_lengths"]
N = data["N"]

print(f"Index loaded successfully!")
print(f"Indexed documents: {N}")
print(f"Unique terms: {len(inverted_index)}")
print(f"Books available: {len(books_metadata)}\n")

# -------- PREPROCESS QUERY --------
def tokenize(text):
    """Convert text to lowercase and extract words"""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return text.split()

# -------- BM25 PARAMETERS --------
k1 = 1.5
b = 0.75
avg_dl = sum(doc_lengths.values()) / N

# -------- BM25 SCORING FUNCTION --------
def bm25_score(query_terms):
    """Calculate BM25 scores for all documents matching query terms"""
    scores = {}

    for term in query_terms:
        if term not in inverted_index:
            continue

        df = len(inverted_index[term])
        idf = math.log((N - df + 0.5) / (df + 0.5) + 1)

        for doc_id in inverted_index[term]:
            tf = term_freqs[doc_id][term]
            dl = doc_lengths[doc_id]

            score = idf * ((tf * (k1 + 1)) /
                           (tf + k1 * (1 - b + b * dl / avg_dl)))

            scores[doc_id] = scores.get(doc_id, 0) + score

    return scores

def calculate_proximity_score(tokens, query_terms):
    """Calculate proximity score based on how close query terms appear together"""
    if len(query_terms) <= 1:
        return 0
    
    # Find positions of all query terms
    positions = {term: [] for term in query_terms}
    for idx, token in enumerate(tokens):
        if token in positions:
            positions[token].append(idx)
    
    # Check if all terms are present
    if any(len(pos) == 0 for pos in positions.values()):
        return 0
    
    # Find minimum span containing all query terms
    min_span = float('inf')
    for pos_list in positions[list(positions.keys())[0]]:
        # For each position of the first term, find closest occurrence of other terms
        term_positions = [pos_list]
        for term in query_terms[1:]:
            closest_pos = min(positions[term], key=lambda x: abs(x - pos_list))
            term_positions.append(closest_pos)
        
        span = max(term_positions) - min(term_positions) + 1
        min_span = min(min_span, span)
    
    # Score inversely proportional to span (closer = higher score)
    # Perfect consecutive match (span = len(query_terms)) gets max score
    if min_span == len(query_terms):
        return 50.0  # Exact consecutive phrase match
    elif min_span < len(query_terms) * 3:
        return 30.0 / min_span  # Close proximity
    else:
        return 10.0 / min_span  # Distant terms

def check_exact_phrase(text, query):
    """Check if exact phrase exists in text (case insensitive)"""
    text_lower = text.lower()
    query_lower = query.lower()
    return query_lower in text_lower

def enhanced_search(query_terms, original_query):
    """Enhanced search with phrase matching and proximity scoring"""
    # Get base BM25 scores
    base_scores = bm25_score(query_terms)
    
    # Enhanced scores with phrase and proximity bonuses
    enhanced_scores = {}
    
    for doc_id, base_score in base_scores.items():
        book_id, page_number = doc_id
        
        # Fetch page content from MongoDB
        page_doc = pages_collection.find_one({
            'book_id': book_id,
            'page_number': page_number
        })
        
        if not page_doc:
            enhanced_scores[doc_id] = base_score
            continue
        
        text_content = page_doc['text_content']
        tokens = tokenize(text_content)
        
        # Calculate bonuses
        phrase_bonus = 0
        proximity_bonus = 0
        
        # Check for exact phrase match (highest priority)
        if check_exact_phrase(text_content, original_query):
            phrase_bonus = 100.0  # Large boost for exact phrase
        
        # Calculate proximity score
        proximity_bonus = calculate_proximity_score(tokens, query_terms)
        
        # Combine scores: BM25 + phrase bonus + proximity bonus
        final_score = base_score + phrase_bonus + proximity_bonus
        enhanced_scores[doc_id] = final_score
    
    return sorted(enhanced_scores.items(), key=lambda x: x[1], reverse=True)

# -------- RUN SEARCH --------
query = input("Enter search text: ")
query_terms = tokenize(query)

print(f"\nSearching for: {query}")
print(f"Query terms: {query_terms}\n")

results = enhanced_search(query_terms, query)

if not results:
    print("No results found!")
else:
    print(f"{'='*80}")
    print(f" SEARCH RESULTS - Found {len(results)} matching pages")
    print(f"{'='*80}\n")

    for rank, (doc_id, score) in enumerate(results[:10], 1):   # show top 10
        book_id, page_number = doc_id
        
        # Get book metadata
        book_info = books_metadata.get(book_id, {})
        title = book_info.get('title', 'Unknown')
        domain = book_info.get('domain', 'Unknown')
        
        # Fetch page content from MongoDB
        page_doc = pages_collection.find_one({
            'book_id': book_id,
            'page_number': page_number
        })
        
        if page_doc:
            text_content = page_doc['text_content']
            preview = text_content[:400] + "..." if len(text_content) > 400 else text_content
        else:
            preview = "[Page content not found in database]"
        
        print(f"[{rank}] Score: {round(score, 3)}")
        print(f"Book: {title}")
        print(f"Domain: {domain} | Page: {page_number}")
        print(f"\nPreview:\n{preview}")
        print(f"{'-'*80}\n")
