import json
from collections import Counter

# Input and output files
INPUT_FILE = "data/training_dataset_clean.json"
OUTPUT_FILE = "data/training_dataset_400k.json"
NUM_ENTRIES = 400000

print("=" * 60)
print("CREATING 400K DATASET")
print("=" * 60)

# Read the full dataset
print(f"\nReading full dataset from {INPUT_FILE}...")
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    full_dataset = json.load(f)

print(f"Total entries in full dataset: {len(full_dataset)}")

# Take first 400,000 entries
smaller_dataset = full_dataset[:NUM_ENTRIES]

print(f"Selected first {len(smaller_dataset)} entries")

# Save dataset
print(f"\nSaving 400k dataset to {OUTPUT_FILE}...")
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(smaller_dataset, f, indent=2, ensure_ascii=False)

print(f"✓ Dataset saved successfully!")

# Analyze the dataset
print("\n" + "=" * 60)
print("DATASET STATISTICS")
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

# Unique books and pages
unique_books = set(entry['book_id'] for entry in smaller_dataset)
print(f"Unique books: {len(unique_books)}")

# Average word overlap
avg_overlap = sum(entry['word_overlap_score'] for entry in smaller_dataset) / len(smaller_dataset)
print(f"Average word overlap score: {avg_overlap:.2f}")

print("\n✓ Process completed successfully!")
print("=" * 60)
