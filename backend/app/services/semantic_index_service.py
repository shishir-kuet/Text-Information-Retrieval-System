import math
import os
import pickle
import re
from pathlib import Path
from typing import Any, cast

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.app.config.paths import SEARCH_INDEX_FILE, SEMANTIC_INDEX_FILE, SEMANTIC_META_FILE, SEMANTIC_PAGE_MAP_FILE
from backend.app.config.settings import settings
from backend.app.models import ensure_schema_indexes


def _now_str() -> str:
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def clean_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    return cleaned


def split_into_chunks(text: str, *, min_words: int, max_words: int, target_words: int) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks: list[list[str]] = []
    idx = 0
    total = len(words)

    while idx < total:
        remaining = total - idx
        if remaining <= max_words:
            if remaining < min_words and chunks:
                chunks[-1].extend(words[idx:])
                break
            chunks.append(words[idx:])
            break

        size = min(target_words, max_words)
        if remaining < size + min_words:
            size = max(min_words, remaining - min_words)

        chunk_words = words[idx : idx + size]
        chunks.append(chunk_words)
        idx += size

    return [" ".join(chunk) for chunk in chunks]


def _atomic_pickle_dump(data, target_path: Path) -> None:
    os.makedirs(target_path.parent, exist_ok=True)
    tmp_path = target_path.with_suffix(target_path.suffix + ".tmp")
    with open(tmp_path, "wb") as f:
        pickle.dump(data, f)
    os.replace(tmp_path, target_path)


class SemanticIndexService:
    def __init__(self):
        self.index_file = SEMANTIC_INDEX_FILE
        self.meta_file = SEMANTIC_META_FILE
        self.page_map_file = SEMANTIC_PAGE_MAP_FILE
        self.index: faiss.Index | None = None
        self.meta: dict[int, dict] | None = None
        self.page_map: dict[tuple[int, int], list[int]] | None = None
        self.index_mtime: float | None = None
        self.model: SentenceTransformer | None = None

    def _load_model(self) -> SentenceTransformer:
        if self.model is None:
            # Force CPU + disable low_cpu_mem_usage to avoid occasional
            # meta-tensor loading failures on some torch/transformers combos.
            self.model = SentenceTransformer(
                settings.semantic_model_name,
                device="cpu",
                model_kwargs={"low_cpu_mem_usage": False},
            )
        return self.model

    def index_available(self) -> bool:
        return self.index_file.exists() and self.meta_file.exists() and self.page_map_file.exists()

    def load_index(self, force_reload: bool = False) -> tuple[faiss.Index, dict[int, dict], dict[tuple[int, int], list[int]]]:
        if not self.index_available():
            raise FileNotFoundError("Semantic index files not found")

        mtime = max(
            self.index_file.stat().st_mtime,
            self.meta_file.stat().st_mtime,
            self.page_map_file.stat().st_mtime,
        )
        if self.index is not None and not force_reload and self.index_mtime == mtime:
            return self.index, self.meta or {}, self.page_map or {}

        self.index = faiss.read_index(str(self.index_file))
        with open(self.meta_file, "rb") as f:
            self.meta = pickle.load(f)
        with open(self.page_map_file, "rb") as f:
            self.page_map = pickle.load(f)
        self.index_mtime = mtime
        index = self.index
        meta = self.meta
        page_map = self.page_map
        if index is None or meta is None or page_map is None:
            raise RuntimeError("Failed to load semantic index artifacts")
        return index, meta, page_map

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        model = self._load_model()
        embeddings = model.encode(
            texts,
            batch_size=64,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return np.asarray(embeddings, dtype="float32")

    def embed_query(self, query: str) -> np.ndarray:
        vector = self.embed_texts([query])
        return vector[0]

    def semantic_top_chunks(self, query_embedding: np.ndarray, top_k: int) -> list[tuple[int, float]]:
        index, _, _ = self.load_index()
        query = np.asarray([query_embedding], dtype="float32")
        scores, ids = cast(Any, index).search(query, top_k)
        results: list[tuple[int, float]] = []
        for chunk_id, score in zip(ids[0], scores[0]):
            if chunk_id == -1:
                continue
            results.append((int(chunk_id), float(score)))
        return results

    def semantic_scores_for_pages(self, query: str, page_ids: list[tuple[int, int]], top_k: int) -> dict[tuple[int, int], float]:
        query = (query or "").strip()
        if not query:
            return {pid: 0.0 for pid in page_ids}

        index, _, page_map = self.load_index()
        if index.ntotal == 0:
            return {pid: 0.0 for pid in page_ids}

        query_embedding = self.embed_query(query)
        top_k = max(top_k, 1)
        top_hits = self.semantic_top_chunks(query_embedding, top_k=top_k)
        chunk_scores = {chunk_id: score for chunk_id, score in top_hits}

        scores: dict[tuple[int, int], float] = {}
        for page_id in page_ids:
            chunk_ids = page_map.get(page_id) or []
            if not chunk_ids:
                scores[page_id] = 0.0
                continue
            best = 0.0
            for chunk_id in chunk_ids:
                score = chunk_scores.get(chunk_id)
                if score is not None and score > best:
                    best = score
            scores[page_id] = float(best)
        return scores


def _create_faiss_index(dim: int, total_vectors: int):
    if total_vectors <= 0:
        base = faiss.IndexFlatIP(dim)
        return faiss.IndexIDMap2(base)

    if total_vectors < 10000:
        base = faiss.IndexFlatIP(dim)
        return faiss.IndexIDMap2(base)

    nlist = int(math.sqrt(total_vectors))
    nlist = max(64, min(nlist, 4096))
    quantizer = faiss.IndexFlatIP(dim)
    index = faiss.IndexIVFFlat(quantizer, dim, nlist, faiss.METRIC_INNER_PRODUCT)
    return faiss.IndexIDMap2(index)


def _train_index(index, training_vectors: np.ndarray):
    if hasattr(index, "is_trained") and not index.is_trained:
        if training_vectors.size == 0:
            raise ValueError("Not enough vectors to train semantic index")
        index.train(training_vectors)


def build_semantic_index(*, full_rebuild: bool = False):
    """Build the FAISS semantic index and chunk metadata from the local search index."""
    ensure_schema_indexes()
    if not SEARCH_INDEX_FILE.exists():
        return {
            "mode": "full" if full_rebuild else "incremental",
            "indexed_books": 0,
            "indexed_chunks": 0,
            "empty_pages": 0,
            "total_chunks": 0,
            "build_date": _now_str(),
            "skipped": True,
            "message": "Search index not found",
        }

    service = SemanticIndexService()

    index = None
    meta: dict[int, dict] = {}
    page_map: dict[tuple[int, int], list[int]] = {}
    next_chunk_id = 1

    model = service._load_model()
    dim_raw = model.get_sentence_embedding_dimension()
    if dim_raw is None:
        raise ValueError("Sentence transformer returned no embedding dimension")
    dim = int(dim_raw)

    with open(SEARCH_INDEX_FILE, "rb") as f:
        search_index = pickle.load(f)

    page_texts = search_index.get("page_texts", {}) or {}
    books_metadata = search_index.get("books_metadata", {}) or {}

    if not page_texts:
        return {
            "mode": "full" if full_rebuild else "incremental",
            "indexed_books": 0,
            "indexed_chunks": 0,
            "empty_pages": 0,
            "total_chunks": 0,
            "build_date": _now_str(),
            "skipped": True,
            "message": "No page text available in search index",
        }

    if index is None:
        index = _create_faiss_index(dim, 0)

    unique_books = sorted({int(book_id) for book_id, _page_number in page_texts.keys()})

    training_texts: list[str] = []
    total_chunks = 0
    empty_pages = 0

    for (book_id, page_number), raw_text in page_texts.items():
        text = clean_text(raw_text)
        if not text:
            empty_pages += 1
            continue
        chunks = split_into_chunks(
            text,
            min_words=settings.chunk_min_words,
            max_words=settings.chunk_max_words,
            target_words=settings.chunk_target_words,
        )
        total_chunks += len(chunks)
        for chunk in chunks:
            if len(training_texts) < 5000:
                training_texts.append(chunk)

    if total_chunks == 0:
        return {
            "mode": "full" if full_rebuild else "incremental",
            "indexed_books": len(unique_books),
            "indexed_chunks": 0,
            "empty_pages": empty_pages,
            "total_chunks": 0,
            "build_date": _now_str(),
            "skipped": True,
            "message": "No chunkable text found",
        }

    if index.ntotal == 0:
        index = _create_faiss_index(dim, total_chunks)
    if hasattr(index, "is_trained") and not index.is_trained:
        train_vectors = model.encode(
            training_texts,
            batch_size=64,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        _train_index(index, np.asarray(train_vectors, dtype="float32"))

    indexed_chunks = 0
    embed_texts: list[str] = []
    embed_ids: list[int] = []

    def flush_embeddings():
        nonlocal indexed_chunks
        if not embed_texts:
            return
        vectors = model.encode(
            embed_texts,
            batch_size=64,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        vectors = np.asarray(vectors, dtype="float32")
        ids = np.asarray(embed_ids, dtype="int64")
        cast(Any, index).add_with_ids(vectors, ids)
        indexed_chunks += len(embed_ids)
        embed_texts.clear()
        embed_ids.clear()

    for (book_id, page_number), raw_text in page_texts.items():
        text = clean_text(raw_text)
        if not text:
            continue

        book_name = (books_metadata.get(book_id) or {}).get("title") or (books_metadata.get(str(book_id)) or {}).get("title") or "Unknown"
        chunks = split_into_chunks(
            text,
            min_words=settings.chunk_min_words,
            max_words=settings.chunk_max_words,
            target_words=settings.chunk_target_words,
        )

        for chunk_index, chunk_text in enumerate(chunks, start=1):
            chunk_id = next_chunk_id
            next_chunk_id += 1

            meta[chunk_id] = {
                "chunk_id": chunk_id,
                "book_id": book_id,
                "book_name": book_name,
                "page_number": page_number,
                "chunk_index": chunk_index,
                "chunk_text": chunk_text,
            }
            page_map.setdefault((book_id, page_number), []).append(chunk_id)

            embed_texts.append(chunk_text)
            embed_ids.append(chunk_id)

            if len(embed_texts) >= 128:
                flush_embeddings()

    flush_embeddings()

    os.makedirs(SEMANTIC_INDEX_FILE.parent, exist_ok=True)
    faiss.write_index(index, str(SEMANTIC_INDEX_FILE))
    _atomic_pickle_dump(meta, SEMANTIC_META_FILE)
    _atomic_pickle_dump(page_map, SEMANTIC_PAGE_MAP_FILE)

    return {
        "mode": "full" if full_rebuild else "incremental",
        "indexed_books": len(unique_books),
        "indexed_chunks": indexed_chunks,
        "empty_pages": empty_pages,
        "total_chunks": len(meta),
        "build_date": _now_str(),
        "skipped": False,
        "message": None,
    }
