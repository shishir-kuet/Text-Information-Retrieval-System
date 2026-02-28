import json
import re
import math
from collections import defaultdict, Counter
import pickle

# -------- LOAD PAGES JSON --------
with open("american_revolution_pages.json", "r", encoding="utf-8") as f:
    pages = json.load(f)

# -------- TEXT PREPROCESSING --------
def tokenize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return text.split()

# -------- DATA STRUCTURES --------
inverted_index = defaultdict(list)   # term → pages
term_freqs = {}                      # page → Counter(term)
doc_lengths = {}                     # page → length

# -------- BUILD INDEX --------
for page_no, text in pages.items():
    tokens = tokenize(text)
    freq = Counter(tokens)

    term_freqs[int(page_no)] = freq
    doc_lengths[int(page_no)] = sum(freq.values())

    for term in freq:
        inverted_index[term].append(int(page_no))

N = len(pages)

# -------- SAVE INDEX --------
index_data = {
    "pages": pages,
    "inverted_index": dict(inverted_index),
    "term_freqs": term_freqs,
    "doc_lengths": doc_lengths,
    "N": N
}

with open("index.pkl", "wb") as f:
    pickle.dump(index_data, f)

print("Index built successfully.")
print("Total pages indexed:", N)
