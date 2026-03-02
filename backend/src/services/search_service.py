"""BM25-based full-text search over the pre-built inverted index."""

import math

from backend.src.models.page import PageModel
from backend.src.services.tokenizer_service import tokenize

# BM25 hyper-parameters
K1 = 1.5
B = 0.75

# Maximum BM25 candidates fetched before MongoDB preview enrichment
TOP_CANDIDATES = 200


def bm25_score(query_terms: list, inverted_index: dict, term_freqs: dict,
               doc_lengths: dict, N: int) -> dict:
    """Return {page_id: bm25_score} for all pages that match at least one term."""
    avg_dl = sum(doc_lengths.values()) / N if N > 0 else 1
    scores = {}

    for term in query_terms:
        if term not in inverted_index:
            continue
        postings = inverted_index[term]
        df = len(postings)
        idf = math.log((N - df + 0.5) / (df + 0.5) + 1)

        for page_id, tf in postings.items():
            dl = doc_lengths.get(page_id, avg_dl)
            tf_norm = (tf * (K1 + 1)) / (tf + K1 * (1 - B + B * dl / avg_dl))
            scores[page_id] = scores.get(page_id, 0) + idf * tf_norm

    return scores


def calculate_proximity_score(tokens: list, query_terms: list) -> float:
    """Bonus for query terms appearing close together in a page."""
    if len(query_terms) < 2:
        return 0.0
    positions = {}
    for i, token in enumerate(tokens):
        if token in query_terms:
            positions.setdefault(token, []).append(i)
    if len(positions) < 2:
        return 0.0

    # Minimum spanning window over one position per term
    best_span = float("inf")
    pos_lists = list(positions.values())
    indices = [0] * len(pos_lists)

    while True:
        window_min = min(pos_lists[i][indices[i]] for i in range(len(pos_lists)))
        window_max = max(pos_lists[i][indices[i]] for i in range(len(pos_lists)))
        best_span = min(best_span, window_max - window_min)

        # Advance the list with the smallest current position
        min_list = min(range(len(pos_lists)), key=lambda i: pos_lists[i][indices[i]])
        indices[min_list] += 1
        if indices[min_list] >= len(pos_lists[min_list]):
            break

    if best_span <= 5:
        return 50.0
    elif best_span <= 15:
        return 30.0
    elif best_span <= 30:
        return 10.0
    return 0.0


def check_exact_phrase(text: str, query: str) -> bool:
    """Return True if the original query appears verbatim in the text."""
    return query.lower() in text.lower()


def enhanced_search(query_terms: list, original_query: str,
                    inverted_index: dict, term_freqs: dict,
                    doc_lengths: dict, books_metadata: dict, N: int,
                    db) -> list:
    """
    Full search pipeline:
    1. BM25 scoring over inverted index
    2. Limit to TOP_CANDIDATES
    3. Batch-fetch page text from MongoDB
    4. Apply proximity + exact-phrase bonuses
    5. Return top-10 results
    """
    page_model = PageModel(db)
    scores = bm25_score(query_terms, inverted_index, term_freqs, doc_lengths, N)

    if not scores:
        return []

    # Take top candidates by BM25 before expensive DB fetch
    top_candidates = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:TOP_CANDIDATES]
    candidate_ids = [pid for pid, _ in top_candidates]
    candidate_scores = dict(top_candidates)

    # Single batch query — fetch text + display_page_number together
    pages = page_model.find_by_ids(candidate_ids)

    # Build a richer page data map that includes display_page_number
    page_data_map = {p["page_id"]: p for p in pages}

    final_scores = {}
    for page_id, base_score in candidate_scores.items():
        text = page_data_map.get(page_id, {}).get("text_content", "")
        tokens = tokenize(text)
        proximity_bonus = calculate_proximity_score(tokens, query_terms)
        exact_bonus = 100.0 if check_exact_phrase(text, original_query) else 0.0
        final_scores[page_id] = base_score + proximity_bonus + exact_bonus

    top_results = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)[:10]

    results = []
    for page_id, score in top_results:
        meta = books_metadata.get(page_id, {})
        page_data = page_data_map.get(page_id, {})
        text = page_data.get("text_content", "")
        physical_page = meta.get("page_number", "?")
        display_page = page_data.get(
            "display_page_number",
            str(physical_page) if physical_page != "?" else "?"
        )
        preview = text[:300].replace("\n", " ") if text else "(no text)"
        results.append({
            "page_id": page_id,
            "score": round(score, 4),
            "book_title": meta.get("book_title", "Unknown"),
            "page_number": physical_page,
            "display_page_number": display_page,
            "domain": meta.get("domain", "Unknown"),
            "preview": preview,
        })

    return results
