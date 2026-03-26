from datetime import datetime


BOOK_STATUS_UPLOADED = "uploaded"
BOOK_STATUS_PROCESSED = "processed"
BOOK_STATUS_INDEXED = "indexed"


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def build_book_document(*, book_id: int, title: str, domain: str, file_path: str, num_pages: int, file_size_mb: float, date_added: str | None = None) -> dict:
    ts = date_added or now_str()
    return {
        "book_id": book_id,
        "title": title,
        "author": None,
        "year": None,
        "domain": domain,
        "file_name": f"{title}.pdf",
        "stored_file_name": f"book_{book_id:03d}.pdf",
        "file_path": file_path,
        "num_pages": num_pages,
        "file_size_mb": file_size_mb,
        "status": BOOK_STATUS_PROCESSED,
        "ingestion_method": "ocr",
        "is_downloadable": True,
        "date_added": ts,
        "updated_at": ts,
    }


def build_page_document(*, book_id: int, page_number: int, text_content: str, created_at: str | None = None) -> dict:
    ts = created_at or now_str()
    words = text_content.split()
    return {
        "page_id": f"{book_id}_{page_number}",
        "book_id": book_id,
        "page_number": page_number,
        "display_page_number": str(page_number),
        "text_content": text_content,
        "word_count": len(words),
        "char_count": len(text_content),
        "token_count": len(words),
        "created_at": ts,
    }


def ensure_book_document(doc: dict) -> dict:
    ts = doc.get("date_added") or now_str()
    out = dict(doc)
    out.setdefault("author", None)
    out.setdefault("year", None)
    out.setdefault("file_name", f"{doc.get('title', 'unknown')}.pdf")
    out.setdefault("stored_file_name", f"book_{int(doc.get('book_id', 0)):03d}.pdf" if doc.get("book_id") is not None else None)
    out.setdefault("status", BOOK_STATUS_INDEXED)
    out.setdefault("ingestion_method", "ocr")
    out.setdefault("is_downloadable", True)
    out.setdefault("date_added", ts)
    out.setdefault("updated_at", ts)
    return out


def ensure_page_document(doc: dict) -> dict:
    text = doc.get("text_content", "") or ""
    out = dict(doc)
    out.setdefault("display_page_number", str(doc.get("page_number", "")))
    out.setdefault("word_count", len(text.split()))
    out.setdefault("char_count", len(text))
    out.setdefault("token_count", len(text.split()))
    out.setdefault("created_at", now_str())
    return out


def ensure_user_document(doc: dict) -> dict:
    out = dict(doc)
    ts = out.get("created_at") or now_str()
    out.setdefault("name", "")
    out.setdefault("email", "")
    out.setdefault("password_hash", "")
    out.setdefault("role", "user")
    out.setdefault("created_at", ts)
    out.setdefault("updated_at", ts)
    return out


def ensure_search_log_document(doc: dict) -> dict:
    out = dict(doc)
    out.setdefault("user_id", None)
    out.setdefault("query_text", "")
    out.setdefault("normalized_query", [])
    out.setdefault("total_results", 0)
    out.setdefault("top_results", [])
    out.setdefault("latency_ms", 0)
    out.setdefault("created_at", now_str())
    return out
