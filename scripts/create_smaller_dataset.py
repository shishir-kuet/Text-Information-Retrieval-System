import json
from datetime import datetime
from collections import Counter

# Input and output files
INPUT_FILE = "data/training_dataset_clean.json"
OUTPUT_FILE = "data/training_dataset_9000.json"
NUM_ENTRIES = 9000

print("=" * 60)
print("CREATING SMALLER DATASET")
print("=" * 60)

# Read the full dataset
print(f"\nReading full dataset from {INPUT_FILE}...")
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    full_dataset = json.load(f)

print(f"Total entries in full dataset: {len(full_dataset)}")

# Take first 9000 entries
smaller_dataset = full_dataset[:NUM_ENTRIES]

print(f"Selected first {len(smaller_dataset)} entries")

# Save smaller dataset
print(f"\nSaving smaller dataset to {OUTPUT_FILE}...")
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(smaller_dataset, f, indent=2, ensure_ascii=False)

print(f"✓ Smaller dataset saved successfully!")

# Analyze the dataset
print("\n" + "=" * 60)
print("DATASET ANALYSIS")
print("=" * 60)

# Count relevance labels
label_counts = Counter(entry['relevance_label'] for entry in smaller_dataset)
print(f"\nRelevance Label Distribution:")
print(f"  Label 0 (unrelated): {label_counts[0]}")
print(f"  Label 1 (same book, overlap): {label_counts[1]}")
print(f"  Label 2 (source page): {label_counts[2]}")

# Analyze queries
unique_queries = set(entry['query'] for entry in smaller_dataset)
print(f"\nUnique queries: {len(unique_queries)}")

# Average word overlap
avg_overlap = sum(entry['word_overlap_score'] for entry in smaller_dataset) / len(smaller_dataset)
print(f"Average word overlap score: {avg_overlap:.2f}")

# Show query generation patterns
print("\n" + "=" * 60)
print("QUERY GENERATION EXPLANATION")
print("=" * 60)
print("""
Each query in the dataset is generated FROM a source page's text content.

The generation process:
1. Tokenize the page text and remove stopwords
2. Extract most frequent keywords (unigrams)
3. Extract common 2-word phrases (bigrams)
4. Extract common 3-word phrases (trigrams)
5. Randomly generate 3-5 queries by combining:
   - 2-4 top keywords together
   - Top bigrams (phrases)
   - Top trigrams (longer phrases)
   - Mixed combinations

For example, if a page discusses "binary search trees":
- Unigram query: "binary search tree algorithm"
- Bigram query: "binary search tree"
- Trigram query: "binary search tree definition"
- Mixed query: "search tree data structure"

Each query is then paired with:
- The source page (relevance_label = 2)
- Pages from same book with word overlap (relevance_label = 1)
- Unrelated pages from other books (relevance_label = 0)
""")

print("\n" + "=" * 60)
print("SAMPLE ENTRIES WITH QUERY ANALYSIS")
print("=" * 60)

# Show examples of label 2 (source pages)
source_pages = [e for e in smaller_dataset if e['relevance_label'] == 2][:5]

for i, entry in enumerate(source_pages, 1):
    print(f"\nExample {i}:")
    print(f"  Query: '{entry['query']}'")
    print(f"  Book ID: {entry['book_id']}, Page: {entry['page_number']}")
    print(f"  Word Overlap: {entry['word_overlap_score']}")
    print(f"  Relevance: {entry['relevance_label']} (SOURCE PAGE - query generated from this page)")
    print(f"  Snippet: {entry['page_text_snippet'][:100]}...")
    
    # Show that query words appear in snippet
    query_words = entry['query'].split()
    snippet_lower = entry['page_text_snippet'].lower()
    found_words = [w for w in query_words if w in snippet_lower]
    print(f"  → Query words found in snippet: {found_words}")

print("\n" + "=" * 60)
