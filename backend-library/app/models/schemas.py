from datetime import datetime

BOOK_STATUS_UPLOADED = "uploaded"
BOOK_STATUS_PROCESSED = "processed"
BOOK_STATUS_INDEXED = "indexed"


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def build_book_document(*, book_id: int, title: str, author: str | None = None, year: int | None = None, domain: str = "Library", file_name: str | None = None, stored_file_name: str | None = None, file_path: str | None = None, num_pages: int | None = None, file_size_mb: float | None = None, status: str = BOOK_STATUS_UPLOADED) -> dict:
    ts = now_str()
    safe_title = title.strip() if title else "Untitled"
    return {
        "book_id": book_id,
        "title": safe_title,
        "author": author,
        "year": year,
        "domain": domain,
        "file_name": file_name or f"{safe_title}.pdf",
        "stored_file_name": stored_file_name or f"book_{book_id:03d}.pdf",
        "file_path": file_path,
        "num_pages": num_pages,
        "file_size_mb": file_size_mb,
        "status": status,
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
    out = dict(doc)
    out.setdefault("author", None)
    out.setdefault("year", None)
    out.setdefault("domain", "Library")
    out.setdefault("file_name", f"{out.get('title', 'Untitled')}.pdf")
    if out.get("book_id") is not None:
        out.setdefault("stored_file_name", f"book_{int(out.get('book_id')):03d}.pdf")
    out.setdefault("status", BOOK_STATUS_UPLOADED)
    out.setdefault("is_downloadable", True)
    out.setdefault("date_added", now_str())
    out.setdefault("updated_at", now_str())
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
