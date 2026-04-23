import json
import re
from collections import Counter
from datetime import datetime

# -------- CONFIGURATION --------
INPUT_FILE = "data/training_dataset_20260306_014411.json"  # Main dataset with all entries
OUTPUT_FILE = "data/training_dataset_clean.json"

print("=" * 60)
print("QUERY CLEANING AND REGENERATION")
print("=" * 60)

# -------- STOPWORDS AND METADATA --------
STOPWORDS = {
    'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are', 'was', 'were',
    'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
    'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'who', 'when',
    'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most',
    'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
    'than', 'too', 'very', 'and', 'but', 'or', 'if', 'then', 'for', 'with',
    'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'to', 'from', 'up', 'down', 'in', 'out', 'of', 'by', 'between', 'among',
    'until', 'while', 'of', 'per', 'also', 'just', 'being', 'over', 'under'
}

METADATA_WORDS = {
    'chapter', 'figure', 'table', 'press', 'editor', 'copyright', 'page',
    'publication', 'published', 'isbn', 'edition', 'publisher', 'author',
    'volume', 'issue', 'journal', 'proceedings', 'conference', 'university',
    'department', 'acknowledgment', 'preface', 'appendix', 'bibliography',
    'references', 'index', 'contents', 'introduction', 'conclusion', 'abstract'
}

# Combine all words to filter
FILTER_WORDS = STOPWORDS | METADATA_WORDS

# -------- TEXT PROCESSING --------
def tokenize(text):
    """Convert text to lowercase and extract words"""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = text.split()
    return [t for t in tokens if len(t) > 2]  # Remove very short words

def remove_filter_words(tokens):
    """Remove stopwords and metadata words"""
    return [t for t in tokens if t not in FILTER_WORDS]

def extract_ngrams(tokens, n):
    """Extract n-grams from tokens"""
    ngrams = []
    for i in range(len(tokens) - n + 1):
        ngram = ' '.join(tokens[i:i+n])
        # Skip if any token in ngram is a filter word
        if not any(word in FILTER_WORDS for word in tokens[i:i+n]):
            ngrams.append(ngram)
    return ngrams

def is_good_phrase(phrase):
    """Check if phrase is a good candidate query"""
    words = phrase.split()
    
    # Must be 2-4 words
    if len(words) < 2 or len(words) > 4:
        return False
    
    # Should not contain only numbers
    if all(word.isdigit() for word in words):
        return False
    
    # Should not be all single character words
    if all(len(word) <= 2 for word in words):
        return False
    
    return True

# -------- QUERY GENERATION --------
def generate_query_from_snippet(snippet):
    """Generate a meaningful 2-4 word query from text snippet"""
    
    if not snippet or len(snippet.strip()) < 10:
        return "unknown topic"
    
    # Tokenize
    tokens = tokenize(snippet)
    
    if len(tokens) < 2:
        return "unknown topic"
    
    # Remove filter words
    filtered_tokens = remove_filter_words(tokens)
    
    if len(filtered_tokens) < 2:
        # Fallback: use original tokens but remove only stopwords
        filtered_tokens = [t for t in tokens if t not in STOPWORDS]
    
    if len(filtered_tokens) < 2:
        return ' '.join(tokens[:2])  # Last resort
    
    # Collect candidate phrases
    candidates = []
    
    # Extract bigrams (2-word phrases)
    if len(filtered_tokens) >= 2:
        bigrams = extract_ngrams(filtered_tokens, 2)
        candidates.extend(bigrams)
    
    # Extract trigrams (3-word phrases)
    if len(filtered_tokens) >= 3:
        trigrams = extract_ngrams(filtered_tokens, 3)
        candidates.extend(trigrams)
    
    # Extract 4-grams
    if len(filtered_tokens) >= 4:
        fourgrams = extract_ngrams(filtered_tokens, 4)
        candidates.extend(fourgrams)
    
    # Filter and count candidates
    good_candidates = [c for c in candidates if is_good_phrase(c)]
    
    if not good_candidates:
        # Fallback: use first 2-3 filtered tokens
        num_words = min(3, len(filtered_tokens))
        return ' '.join(filtered_tokens[:num_words])
    
    # Count frequency of each candidate
    candidate_freq = Counter(good_candidates)
    
    # Get most common phrases
    # Prefer longer phrases if they have good frequency
    sorted_candidates = sorted(
        candidate_freq.items(),
        key=lambda x: (x[1], len(x[0].split())),  # Sort by frequency, then length
        reverse=True
    )
    
    # Return the best candidate
    return sorted_candidates[0][0]

# -------- MAIN PROCESSING --------
def clean_dataset():
    """Load dataset, regenerate queries, and save cleaned version"""
    
    print(f"\nLoading dataset from {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    print(f"Total entries: {len(dataset):,}")
    
    print("\nRegenerating queries from page snippets...")
    
    # Statistics
    query_changes = 0
    query_length_dist = Counter()
    
    # Process each entry
    for i, entry in enumerate(dataset):
        if (i + 1) % 10000 == 0:
            print(f"  Processed {i+1:,}/{len(dataset):,} entries...")
        
        snippet = entry.get('page_text_snippet', '')
        old_query = entry.get('query', '')
        
        # Generate new query
        new_query = generate_query_from_snippet(snippet)
        
        # Update entry
        if new_query != old_query:
            query_changes += 1
        
        entry['query'] = new_query
        
        # Track query length
        query_length = len(new_query.split())
        query_length_dist[query_length] += 1
    
    print(f"\n✓ Query regeneration complete!")
    print(f"  Queries changed: {query_changes:,} ({100*query_changes/len(dataset):.1f}%)")
    
    # Save cleaned dataset
    print(f"\nSaving cleaned dataset to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Cleaned dataset saved successfully!")
    
    # Display statistics
    print("\n" + "=" * 60)
    print("CLEANING STATISTICS")
    print("=" * 60)
    
    print(f"\nQuery length distribution:")
    for length in sorted(query_length_dist.keys()):
        count = query_length_dist[length]
        pct = 100 * count / len(dataset)
        print(f"  {length} words: {count:,} ({pct:.1f}%)")
    
    # Show unique queries
    unique_queries = len(set(entry['query'] for entry in dataset))
    print(f"\nUnique queries: {unique_queries:,}")
    
    # Show examples
    print("\n" + "=" * 60)
    print("SAMPLE BEFORE/AFTER EXAMPLES")
    print("=" * 60)
    
    # Reload original to show comparison
    print("\nLoading original dataset for comparison...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        original_dataset = json.load(f)
    
    # Show 5 random examples
    import random
    sample_indices = random.sample(range(len(dataset)), min(5, len(dataset)))
    
    for idx in sample_indices:
        original = original_dataset[idx]
        cleaned = dataset[idx]
        
        print(f"\nExample:")
        print(f"  Old query: '{original['query']}'")
        print(f"  New query: '{cleaned['query']}'")
        print(f"  Snippet: {cleaned['page_text_snippet'][:100]}...")
        print(f"  Book: {cleaned['book_id']}, Page: {cleaned['page_number']}")

# -------- EXECUTION --------
if __name__ == "__main__":
    try:
        clean_dataset()
        print("\n" + "=" * 60)
        print("✓ PROCESS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
