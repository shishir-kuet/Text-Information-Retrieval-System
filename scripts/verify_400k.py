import json
from collections import Counter

print("Verifying 9000 dataset...")
with open('data/training_dataset_9000.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"\n✓ Total entries: {len(data):,}")

labels = Counter(d['relevance_label'] for d in data)
print(f"\nLabel distribution:")
print(f"  Label 0 (unrelated): {labels[0]:,}")
print(f"  Label 1 (same book): {labels[1]:,}")
print(f"  Label 2 (source page): {labels[2]:,}")

unique_queries = len(set(d['query'] for d in data))
print(f"\nUnique queries: {unique_queries:,}")

print(f"\nSample queries:")
sample_queries = list(set(d['query'] for d in data[:100]))[:10]
for q in sample_queries:
    print(f"  - {q}")
