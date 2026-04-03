import math
import pickle
import re
from pathlib import Path

from backend.app.config.database import get_database
from backend.app.config.paths import SEARCH_INDEX_FILE
from backend.app.models import ensure_page_document
from backend.app.utils.storage import resolve_pdf_path


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
    def __init__(self):
        self.db = get_database()
        self.pages = self.db["pages"]
        self.books = self.db["books"]
        self.index_file = SEARCH_INDEX_FILE
        self.index_data = None
        self.index_mtime = None

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

    def search(self, query: str, top_k: int = 10):
        query = (query or "").strip()
        if not query:
            return []

        query_terms = _tokenize(query)
        if not query_terms:
            return []

        data = self.load_index()
        books_metadata = data["books_metadata"]

        ranked = sorted(self._bm25_scores(query_terms).items(), key=lambda item: item[1], reverse=True)
        if not ranked:
            return []

        candidates = ranked[: max(top_k * 3, top_k)]
        page_filter = [
            {"book_id": book_id, "page_number": page_number}
            for (book_id, page_number), _ in candidates
        ]

        page_map = {}
        if page_filter:
            for raw_page in self.pages.find(
                {"$or": page_filter},
                {"book_id": 1, "page_number": 1, "page_id": 1, "text_content": 1, "display_page_number": 1},
            ):
                page = ensure_page_document(raw_page)
                key = (page.get("book_id"), page.get("page_number"))
                page_map[key] = page

        results = []

        for (book_id, page_number), score in ranked:
            page = page_map.get((book_id, page_number))
            if not page:
                continue

            text_content = page.get("text_content", "")
            book_info = books_metadata.get(book_id, {})

            results.append(
                {
                    "book_id": book_id,
                    "title": book_info.get("title", "Unknown"),
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
        raw_page = self.pages.find_one({"page_id": page_id})
        if not raw_page:
            return None

        page = ensure_page_document(raw_page)
        book = self.books.find_one({"book_id": page.get("book_id")}) or {}
        num_pages = book.get("num_pages")
        if not num_pages:
            try:
                num_pages = self.pages.count_documents({"book_id": page.get("book_id")})
            except Exception:
                num_pages = None

        return {
            "page_id": page.get("page_id"),
            "book_id": page.get("book_id"),
            "page_number": page.get("page_number"),
            "display_page_number": page.get("display_page_number"),
            "text_content": page.get("text_content", ""),
            "snippet": _snippet(page.get("text_content", ""), []),
            "book": {
                "book_id": book.get("book_id"),
                "title": book.get("title"),
                "domain": book.get("domain"),
                "author": book.get("author"),
                "year": book.get("year"),
                "num_pages": num_pages,
            },
        }

    def get_book_download(self, book_id: int):
        book = self.books.find_one({"book_id": book_id})
        if not book:
            return None

        abs_path, pdf_url = resolve_pdf_path(book.get("file_path"))
        if abs_path is None or not abs_path.exists():
            raise FileNotFoundError("PDF file not found")

        return {
            "book_id": book.get("book_id"),
            "title": book.get("title", "book"),
            "file_path": str(abs_path),
            "pdf_url": pdf_url,
            "file_name": book.get("file_name") or f"{book.get('title', 'book')}.pdf",
        }
