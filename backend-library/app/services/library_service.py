from io import BytesIO
from pathlib import Path

from flask import send_file

from app.config.database import get_database
from app.config.paths import BOOKS_DIR
from app.models import (
    BOOK_STATUS_PROCESSED,
    BOOK_STATUS_UPLOADED,
    build_book_document,
    build_page_document,
    ensure_schema_indexes,
    now_str,
)
from app.utils.pdf_processing import extract_page_text, get_pdf_page_count
from app.utils.storage import make_book_file_path, resolve_pdf_path

CHUNK_MIN_WORDS = 200
CHUNK_MAX_WORDS = 300
CHUNK_TARGET_WORDS = 250


def _next_book_id(db) -> int:
    last = db["books"].find_one(sort=[("book_id", -1)])
    if not last or "book_id" not in last:
        return 1
    return int(last["book_id"]) + 1


def _split_into_chunks(text: str) -> list[str]:
    words = (text or "").split()
    if not words:
        return []

    chunks: list[list[str]] = []
    index = 0
    total = len(words)

    while index < total:
        remaining = total - index
        if remaining <= CHUNK_MAX_WORDS:
            if remaining < CHUNK_MIN_WORDS and chunks:
                chunks[-1].extend(words[index:])
                break
            chunks.append(words[index:])
            break

        size = min(CHUNK_TARGET_WORDS, CHUNK_MAX_WORDS)
        if remaining < size + CHUNK_MIN_WORDS:
            size = max(CHUNK_MIN_WORDS, remaining - CHUNK_MIN_WORDS)

        chunk_words = words[index : index + size]
        chunks.append(chunk_words)
        index += size

    return [" ".join(chunk) for chunk in chunks]


def _build_chunk_doc(*, book_id: int, page_number: int, chunk_index: int, chunk_text: str) -> dict:
    ts = now_str()
    return {
        "chunk_id": f"{book_id}_{page_number}_{chunk_index}",
        "book_id": book_id,
        "page_id": f"{book_id}_{page_number}",
        "page_number": page_number,
        "chunk_index": chunk_index,
        "chunk_text": chunk_text,
        "word_count": len(chunk_text.split()),
        "char_count": len(chunk_text),
        "created_at": ts,
    }


def upload_book(file_storage, title: str, author: str = "", year: str | None = None):
    ensure_schema_indexes()
    db = get_database()
    books = db["books"]

    if not file_storage or not file_storage.filename:
        return None, "missing file"
    if not title or not title.strip():
        return None, "missing title"

    parsed_year = None
    if year:
        try:
            parsed_year = int(year)
        except (TypeError, ValueError):
            return None, "invalid year"

    book_id = _next_book_id(db)
    original_filename = Path(file_storage.filename).name
    stored_file_name = f"book_{book_id:03d}.pdf"
    target_dir = BOOKS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / stored_file_name
    file_storage.save(target_path)

    try:
        num_pages = get_pdf_page_count(target_path)
    except Exception:
        num_pages = None

    file_size_mb = round(target_path.stat().st_size / (1024 * 1024), 2)

    book_doc = build_book_document(
        book_id=book_id,
        title=title.strip(),
        author=author.strip() or None,
        year=parsed_year,
        domain="Library",
        file_name=original_filename,
        stored_file_name=stored_file_name,
        file_path=make_book_file_path(stored_file_name),
        num_pages=num_pages,
        file_size_mb=file_size_mb,
        status=BOOK_STATUS_UPLOADED,
    )
    books.insert_one(book_doc)
    return book_doc, None


def process_book(book_id: int):
    ensure_schema_indexes()
    db = get_database()
    books = db["books"]
    pages = db["pages"]
    page_chunks = db["page_chunks"]

    book = books.find_one({"book_id": book_id})
    if not book:
        return None, "book not found"

    file_path = book.get("file_path")
    abs_path, _ = resolve_pdf_path(file_path)
    if abs_path is None or not abs_path.exists():
        return None, "file not found"

    doc = None
    try:
        doc = __import__("fitz").open(str(abs_path))
        num_pages = len(doc)
        pages.delete_many({"book_id": book_id})
        page_chunks.delete_many({"book_id": book_id})
        pages_batch = []
        chunks_batch = []
        chunk_count = 0

        for page_num in range(num_pages):
            text = extract_page_text(doc, abs_path, page_num)
            page_doc = build_page_document(book_id=book_id, page_number=page_num + 1, text_content=text)
            pages_batch.append(page_doc)
            if len(pages_batch) >= 100:
                pages.insert_many(pages_batch)
                pages_batch = []

            chunks = _split_into_chunks(text)
            for chunk_index, chunk_text in enumerate(chunks, start=1):
                chunks_batch.append(
                    _build_chunk_doc(
                        book_id=book_id,
                        page_number=page_num + 1,
                        chunk_index=chunk_index,
                        chunk_text=chunk_text,
                    )
                )
                chunk_count += 1
                if len(chunks_batch) >= 200:
                    page_chunks.insert_many(chunks_batch)
                    chunks_batch = []

        if pages_batch:
            pages.insert_many(pages_batch)
        if chunks_batch:
            page_chunks.insert_many(chunks_batch)

        books.update_one(
            {"book_id": book_id},
            {"$set": {"status": BOOK_STATUS_PROCESSED, "num_pages": num_pages, "updated_at": now_str()}},
        )

        return {
            "book_id": book_id,
            "num_pages": num_pages,
            "chunk_count": chunk_count,
            "status": BOOK_STATUS_PROCESSED,
        }, None
    finally:
        if doc is not None:
            doc.close()


def list_books(limit: int = 100):
    db = get_database()
    cursor = db["books"].find({}).sort("book_id", 1).limit(limit)
    return list(cursor)


def get_book(book_id: int):
    db = get_database()
    return db["books"].find_one({"book_id": book_id})


def list_pages(book_id: int):
    db = get_database()
    cursor = db["pages"].find({"book_id": book_id}).sort("page_number", 1)
    return list(cursor)


def get_page(page_id: str):
    db = get_database()
    page = db["pages"].find_one({"page_id": page_id})
    if not page:
        return None

    book_id = page.get("book_id")
    book = db["books"].find_one({"book_id": book_id}) if book_id is not None else None
    return {
        **page,
        "book": {
            "book_id": book.get("book_id") if book else None,
            "title": book.get("title") if book else None,
            "domain": book.get("domain") if book else None,
            "author": book.get("author") if book else None,
            "year": book.get("year") if book else None,
            "num_pages": book.get("num_pages") if book else None,
        },
    }


def get_page_text(page_id: str):
    page = get_page(page_id)
    if not page:
        return None
    return page.get("text_content", "") or ""


def get_page_pdf_bytes(page_id: str):
    page = get_page(page_id)
    if not page:
        return None, None

    book_id = page.get("book_id")
    page_number = page.get("page_number")
    if book_id is None or page_number is None:
        return None, None

    book = get_book(int(book_id))
    if not book:
        return None, None

    abs_path, _ = resolve_pdf_path(book.get("file_path"))
    if abs_path is None or not abs_path.exists():
        return None, None

    try:
        src = __import__("fitz").open(str(abs_path))
        try:
            idx = int(page_number) - 1
            if idx < 0 or idx >= src.page_count:
                return None, None
            single = __import__("fitz").open()
            try:
                single.insert_pdf(src, from_page=idx, to_page=idx)
                return single.tobytes(), f"book_{int(book_id):03d}_page_{int(page_number):04d}.pdf"
            finally:
                single.close()
        finally:
            src.close()
    except Exception:
        return None, None


def get_book_pdf_path(book_id: int):
    book = get_book(book_id)
    if not book:
        return None
    abs_path, _ = resolve_pdf_path(book.get("file_path"))
    if abs_path is None or not abs_path.exists():
        return None
    return abs_path
