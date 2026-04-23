import json
import re
from collections import Counter
import sys

# -------- STOPWORDS --------
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
    'until', 'while', 'per', 'also', 'just', 'being', 'over', 'under'
}

# -------- METADATA WORDS --------
METADATA_WORDS = {
    'chapter', 'figure', 'table', 'press', 'editor', 'copyright', 'page',
    'publication', 'published', 'isbn', 'edition', 'publisher', 'author',
    'volume', 'issue', 'journal', 'proceedings', 'conference', 'university',
    'department', 'acknowledgment', 'preface', 'appendix', 'bibliography',
    'references', 'index', 'contents', 'introduction', 'conclusion', 'abstract',
    'acknowledgments', 'dedication', 'foreword', 'prologue', 'epilogue'
}

# -------- HELPER FUNCTIONS --------
def clean_query_text(query):
    """Clean query text: lowercase, remove punctuation/numbers, trim spaces"""
    query = query.lower()
    query = re.sub(r'[^a-z\s]', ' ', query)  # Remove non-alphabetic characters
    query = re.sub(r'\s+', ' ', query)  # Replace multiple spaces with single space
    return query.strip()

def contains_numbers(query):
    """Check if query contains any digit"""
    return bool(re.search(r'\d', query))

def contains_metadata_words(query):
    """Check if query contains metadata words"""
    words = query.lower().split()
    return any(word in METADATA_WORDS for word in words)

def is_mostly_stopwords(query):
    """Check if more than 70% of words are stopwords"""
    words = query.lower().split()
    if len(words) == 0:
        return True
    
    stopword_count = sum(1 for word in words if word in STOPWORDS)
    ratio = stopword_count / len(words)
    return ratio > 0.7

def is_valid_entry(entry):
    """Check if entry meets all quality criteria"""
    query = entry.get('query', '')
    word_overlap = entry.get('word_overlap_score', 0)
    
    # Rule 1: word_overlap_score must be > 0
    if word_overlap == 0:
        return False, "zero_overlap"
    
    # Rule 2: Query must not contain numbers
    if contains_numbers(query):
        return False, "contains_numbers"
    
    # Clean the query
    cleaned_query = clean_query_text(query)
    words = cleaned_query.split()
    
    # Rule 3: Query must have at least 2 words
    if len(words) < 2:
        return False, "too_few_words"
    
    # Rule 4: Query must not have more than 6 words
    if len(words) > 6:
        return False, "too_many_words"
    
    # Rule 5: Query must not be mostly stopwords
    if is_mostly_stopwords(cleaned_query):
        return False, "mostly_stopwords"
    
    # Rule 6: Query must not contain metadata words
    if contains_metadata_words(cleaned_query):
        return False, "contains_metadata"
    
    return True, "valid"

def clean_dataset(input_file, output_file):
    """Clean the dataset by filtering and cleaning entries"""
    
    print("=" * 60)
    print("DATASET CLEANING")
    print("=" * 60)
    print(f"\nInput file: {input_file}")
    print(f"Output file: {output_file}")
    
    # Load dataset
    print(f"\nLoading dataset...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
    except FileNotFoundError:
        print(f"✗ Error: File not found: {input_file}")
        return
    except json.JSONDecodeError:
        print(f"✗ Error: Invalid JSON in file: {input_file}")
        return
    
    print(f"Original dataset size: {len(dataset):,} entries")
    
    # Track removal reasons
    removal_reasons = Counter()
    cleaned_dataset = []
    
    print("\nCleaning entries...")
    for i, entry in enumerate(dataset):
        if (i + 1) % 10000 == 0:
            print(f"  Processed {i+1:,}/{len(dataset):,} entries...")
        
        # Check if entry is valid
        valid, reason = is_valid_entry(entry)
        
        if valid:
            # Clean the query text
            original_query = entry['query']
            cleaned_query = clean_query_text(original_query)
            entry['query'] = cleaned_query
            cleaned_dataset.append(entry)
        else:
            removal_reasons[reason] += 1
    
    print(f"\n✓ Cleaning complete!")
    
    # Statistics
    print("\n" + "=" * 60)
    print("CLEANING STATISTICS")
    print("=" * 60)
    print(f"\nOriginal dataset size: {len(dataset):,}")
    print(f"Cleaned dataset size: {len(cleaned_dataset):,}")
    print(f"Removed entries: {len(dataset) - len(cleaned_dataset):,}")
    print(f"Retention rate: {100 * len(cleaned_dataset) / len(dataset):.1f}%")
    
    print(f"\nRemoval reasons:")
    for reason, count in removal_reasons.most_common():
        print(f"  {reason}: {count:,} ({100*count/len(dataset):.1f}%)")
    
    # Analyze cleaned dataset
    print(f"\nCleaned dataset analysis:")
    label_counts = Counter(e['relevance_label'] for e in cleaned_dataset)
    print(f"  Label 0 (unrelated): {label_counts[0]:,}")
    print(f"  Label 1 (same book): {label_counts[1]:,}")
    print(f"  Label 2 (source page): {label_counts[2]:,}")
    
    unique_queries = len(set(e['query'] for e in cleaned_dataset))
    print(f"  Unique queries: {unique_queries:,}")
    
    avg_words = sum(len(e['query'].split()) for e in cleaned_dataset) / len(cleaned_dataset)
    print(f"  Average query length: {avg_words:.1f} words")
    
    avg_overlap = sum(e['word_overlap_score'] for e in cleaned_dataset) / len(cleaned_dataset)
    print(f"  Average word overlap: {avg_overlap:.2f}")
    
    # Show sample queries
    print(f"\nSample cleaned queries:")
    sample_queries = list(set(e['query'] for e in cleaned_dataset[:100]))[:10]
    for q in sample_queries:
        print(f"  - {q}")
    
    # Save cleaned dataset
    print(f"\nSaving cleaned dataset to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_dataset, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Cleaned dataset saved successfully!")
    print("=" * 60)

# -------- MAIN EXECUTION --------
if __name__ == "__main__":
    # Check if input file provided as argument
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        # Generate output filename
        if input_file.endswith('.json'):
            output_file = input_file.replace('.json', '_cleaned.json')
        else:
            output_file = input_file + '_cleaned.json'
        
        if len(sys.argv) > 2:
            output_file = sys.argv[2]
    else:
        # Default files
        input_file = "data/training_dataset_9000.json"
        output_file = "data/training_dataset_9000_cleaned.json"
    
    try:
        clean_dataset(input_file, output_file)
        print("\n✓ PROCESS COMPLETED SUCCESSFULLY!")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
