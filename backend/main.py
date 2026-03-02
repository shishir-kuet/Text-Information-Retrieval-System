"""
backend/main.py — Interactive BM25 book search CLI.

Usage:
    python backend/main.py
"""

import sys
from pathlib import Path

# Allow imports like `from backend.src.*` when run from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.config.db import get_db
from backend.src.services.index_service import load_index
from backend.src.services.search_service import enhanced_search
from backend.src.services.tokenizer_service import tokenize
from backend.src.utils.logger import get_logger

INDEX_PATH = Path(__file__).resolve().parent / "data" / "search_index.pkl"

logger = get_logger(__name__)


def run():
    logger.info("Loading search index…")
    index = load_index(INDEX_PATH)
    db = get_db()

    print("\n" + "=" * 60)
    print(" Book Search System  (BM25 + Proximity + Exact-Phrase)")
    print("=" * 60)
    print(f" Index: {index['N']} pages  |  {len(index['inverted_index'])} unique terms")
    print(f" Built: {index.get('build_date', 'N/A')}")
    print("=" * 60)
    print(" Type a query and press Enter.  Empty input exits.\n")

    while True:
        try:
            query = input("Search: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            break

        if not query:
            print("Goodbye.")
            break

        query_terms = tokenize(query)
        if not query_terms:
            print("  [WARN] No valid tokens in query.\n")
            continue

        results = enhanced_search(
            query_terms=query_terms,
            original_query=query,
            inverted_index=index["inverted_index"],
            term_freqs=index["term_freqs"],
            doc_lengths=index["doc_lengths"],
            books_metadata=index["books_metadata"],
            N=index["N"],
            db=db,
        )

        if not results:
            print("  No results found.\n")
            continue

        print(f"\n  Top {len(results)} result(s) for '{query}':\n")
        for rank, r in enumerate(results, 1):
            print(f"  [{rank}] {r['book_title']}  (p.{r['page_number']})  "
                  f"[{r['domain']}]  score={r['score']}")
            print(f"       {r['preview'][:200]}…\n")


if __name__ == "__main__":
    run()
