import math
import pickle
import re
from bisect import bisect_right
from pathlib import Path

from backend.app.config.paths import SEARCH_INDEX_FILE
from backend.app.config.settings import settings
from backend.app.services.library_client import LibraryClient
from backend.app.services.semantic_index_service import SemanticIndexService


def _tokenize(text: str):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return text.split()


def _snippet(text: str, query_terms, max_len: int = 220):
    if not text:
        return ""

    text_lower = text.lower()
    hit_pos = -1
    for term in query_terms:
        hit_pos = text_lower.find(term.lower())
        if hit_pos >= 0:
            break

    if hit_pos < 0:
        return text[:max_len] + ("..." if len(text) > max_len else "")

    start = max(0, hit_pos - (max_len // 2))
    end = min(len(text), start + max_len)
    snippet = text[start:end]

    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet


class SearchService:
    PHRASE_BOOST = 8.0
    ORDERED_PROXIMITY_BOOST = 2.5
    PROXIMITY_WINDOW = 20
    SHORT_QUERY_MAX = 3
    MEDIUM_QUERY_MAX = 8

    def __init__(self):
        self.index_file = SEARCH_INDEX_FILE
        self.index_data = None
        self.index_mtime = None
        self.semantic_service = SemanticIndexService()
        self.library_client = LibraryClient()

    def load_index(self, force_reload: bool = False):
        index_path = Path(self.index_file)
        if not index_path.exists():
            raise FileNotFoundError(f"Index file not found: {index_path}")

        mtime = index_path.stat().st_mtime
        if self.index_data is not None and not force_reload and self.index_mtime == mtime:
            return self.index_data

        with open(index_path, "rb") as f:
            self.index_data = pickle.load(f)
            self.index_mtime = mtime
        return self.index_data

    def index_available(self):
        return Path(self.index_file).exists()

    def _bm25_scores(self, query_terms):
        data = self.load_index()
        inverted_index = data["inverted_index"]
        term_freqs = data["term_freqs"]
        doc_lengths = data["doc_lengths"]
        n_docs = data["N"]

        if n_docs <= 0:
            return {}

        k1 = 1.5
        b = 0.75
        avg_dl = sum(doc_lengths.values()) / n_docs
        scores = {}

        for term in query_terms:
            if term not in inverted_index:
                continue

            df = len(inverted_index[term])
            idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1)

            for doc_id in inverted_index[term]:
                tf = term_freqs[doc_id][term]
                dl = doc_lengths[doc_id]
                score = idf * ((tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avg_dl)))
                scores[doc_id] = scores.get(doc_id, 0.0) + score

        return scores

    def normalize_query(self, query: str):
        return _tokenize((query or "").strip())

    def _exact_phrase_hits(self, query_terms, doc_id, term_positions):
        if len(query_terms) < 2:
            return 0

        first_positions = term_positions.get(query_terms[0], {}).get(doc_id, [])
        if not first_positions:
            return 0

        lookup_sets = []
        for term in query_terms[1:]:
            positions = term_positions.get(term, {}).get(doc_id, [])
            if not positions:
                return 0
            lookup_sets.append(set(positions))

        hits = 0
        for start in first_positions:
            if all((start + offset + 1) in lookup_sets[offset] for offset in range(len(lookup_sets))):
                hits += 1

        return hits

    def _best_ordered_span(self, query_terms, doc_id, term_positions):
        if len(query_terms) < 2:
            return None

        lists = []
        for term in query_terms:
            positions = term_positions.get(term, {}).get(doc_id, [])
            if not positions:
                return None
            lists.append(positions)

        best_span = None
        for start in lists[0]:
            prev = start
            valid = True
            for next_positions in lists[1:]:
                idx = bisect_right(next_positions, prev)
                if idx >= len(next_positions):
                    valid = False
                    break
                prev = next_positions[idx]

            if not valid:
                continue

            span = (prev - start) + 1
            if best_span is None or span < best_span:
                best_span = span

        return best_span

    def _phrase_proximity_boost(self, query_terms, doc_id, term_positions):
        if len(query_terms) < 2:
            return 0.0

        exact_hits = self._exact_phrase_hits(query_terms, doc_id, term_positions)
        phrase_boost = self.PHRASE_BOOST * min(exact_hits, 3)

        span = self._best_ordered_span(query_terms, doc_id, term_positions)
        if span is None:
            return float(phrase_boost)

        query_len = len(query_terms)
        proximity_factor = min(1.0, query_len / max(query_len, span))
        proximity_boost = self.ORDERED_PROXIMITY_BOOST * proximity_factor

        if span <= self.PROXIMITY_WINDOW:
            tightness = 1.0 - ((span - query_len) / max(1, self.PROXIMITY_WINDOW - query_len))
            proximity_boost += max(0.0, tightness)

        return float(phrase_boost + proximity_boost)

    def _query_term_coverage(self, query_terms, text: str) -> float:
        if not query_terms or not text:
            return 0.0
        text_lower = text.lower()
        unique_terms = list(dict.fromkeys(query_terms))
        if not unique_terms:
            return 0.0
        hits = sum(1 for term in unique_terms if term in text_lower)
        return hits / float(len(unique_terms))

    def _dynamic_weights(self, query_terms):
        length = len(query_terms)
        if length <= self.SHORT_QUERY_MAX:
            return 0.7, 0.2, 0.1
        if length <= self.MEDIUM_QUERY_MAX:
            return 0.55, 0.35, 0.1
        return 0.4, 0.5, 0.1

    def _resolve_title(self, *, book_id: int, page: dict, books_metadata: dict, title_cache: dict[int, str]) -> str:
        book_info = books_metadata.get(book_id, {}) if isinstance(books_metadata, dict) else {}
        title = (book_info.get("title") or page.get("title") or "").strip()
        if title and title.lower() != "unknown":
            return title

        cached = title_cache.get(book_id)
        if cached:
            return cached

        try:
            book_payload = self.library_client.get_book(book_id)
            remote_title = (book_payload.get("title") or "").strip() if isinstance(book_payload, dict) else ""
            if remote_title:
                title_cache[book_id] = remote_title
                return remote_title
        except Exception:
            pass

        return "Unknown"

    def search(self, query: str, top_k: int = 10):
        query = (query or "").strip()
        if not query:
            return []

        query_terms = _tokenize(query)
        if not query_terms:
            return []

        data = self.load_index()
        books_metadata = data["books_metadata"]
        term_positions = data.get("term_positions", {})
        page_texts = data.get("page_texts", {})
        page_records = data.get("page_records", {})

        ranked = sorted(self._bm25_scores(query_terms).items(), key=lambda item: item[1], reverse=True)
        if not ranked:
            return []

        candidates = ranked[: max(50, top_k * 5)]

        page_ids = [(book_id, page_number) for (book_id, page_number), _ in candidates]
        try:
            semantic_scores = self.semantic_service.semantic_scores_for_pages(
                query=query,
                page_ids=page_ids,
                top_k=max(settings.semantic_top_k, top_k * 40),
            )
        except Exception:
            semantic_scores = {pid: 0.0 for pid in page_ids}

        reranked = []
        for (book_id, page_number), bm25_score in candidates:
            doc_id = (book_id, page_number)
            page = page_records.get(f"{book_id}_{page_number}") or {}
            text_content = page_texts.get(doc_id, "") or page.get("text_content", "") or ""
            if not text_content:
                continue

            boost = self._phrase_proximity_boost(query_terms, doc_id, term_positions)
            bm25_total = float(bm25_score) + boost
            semantic_score = float(semantic_scores.get(doc_id, 0.0))
            exact_match = self._query_term_coverage(query_terms, text_content)
            reranked.append((bm25_total, float(bm25_score), semantic_score, exact_match, doc_id, page))

        if not reranked:
            return []

        bm25_max = max(item[0] for item in reranked) or 1.0
        semantic_max = max(item[2] for item in reranked) or 1.0

        bm25_w, semantic_w, exact_w = self._dynamic_weights(query_terms)

        scored = []
        for bm25_total, bm25_raw, semantic_score, exact_match, doc_id, page in reranked:
            bm25_norm = bm25_total / bm25_max if bm25_max > 0 else 0.0
            semantic_norm = semantic_score / semantic_max if semantic_max > 0 else 0.0
            final_score = (bm25_w * bm25_norm) + (semantic_w * semantic_norm) + (exact_w * exact_match)
            scored.append((final_score, bm25_total, semantic_score, exact_match, bm25_raw, doc_id, page))

        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)

        results = []
        title_cache: dict[int, str] = {}
        for score, _bm25_total, _semantic_score, _exact_match, _bm25_score, (book_id, page_number), page in scored:
            text_content = page.get("text_content", "") or page_texts.get((book_id, page_number), "") or ""
            title = self._resolve_title(book_id=book_id, page=page, books_metadata=books_metadata, title_cache=title_cache)
            results.append(
                {
                    "book_id": book_id,
                    "title": title,
                    "page_id": page.get("page_id", f"{book_id}_{page_number}"),
                    "page_number": page_number,
                    "score": round(float(score), 6),
                    "snippet": _snippet(text_content, query_terms),
                }
            )

            if len(results) >= top_k:
                break

        return results

    def get_page(self, page_id: str):
        payload = self.library_client.get_page(page_id)
        page = payload if isinstance(payload, dict) else {}
        if not page:
            return None
        text_content = page.get("text_content", "") or ""
        return {
            "page_id": page.get("page_id"),
            "book_id": page.get("book_id"),
            "page_number": page.get("page_number"),
            "display_page_number": page.get("display_page_number"),
            "text_content": text_content,
            "snippet": _snippet(text_content, []),
            "book": page.get("book") or {},
        }

    def get_book_download(self, book_id: int):
        book = self.library_client.get_book(book_id)
        if not book:
            return None
        return {
            "book_id": book.get("book_id"),
            "title": book.get("title", "book"),
            "file_name": book.get("file_name") or f"{book.get('title', 'book')}.pdf",
            "download_url": f"/api/library/books/{book_id}/download",
        }
