from pathlib import Path

from backend.app.config.database import get_database
from backend.app.config.paths import BOOKS_DIR, SEARCH_INDEX_FILE, SEMANTIC_INDEX_FILE, SEMANTIC_META_FILE, SEMANTIC_PAGE_MAP_FILE
from backend.app.models import (
    BOOK_STATUS_INDEXED,
    BOOK_STATUS_PROCESSED,
    BOOK_STATUS_UPLOADED,
    build_page_document,
    ensure_schema_indexes,
    now_str,
)
from backend.app.services.build_search_index import build_index
from backend.app.utils.pdf_processing import extract_page_text, get_pdf_page_count
from backend.app.utils.storage import make_book_file_path, resolve_pdf_path


def _next_book_id(db) -> int:
    last = db['books'].find_one(sort=[('book_id', -1)])
    if not last or 'book_id' not in last:
        return 1
    return int(last['book_id']) + 1


def upload_book(file_storage, domain: str, title: str, author: str, year: str | None = None):
    ensure_schema_indexes()
    db = get_database()
    books = db['books']

    if not file_storage or not file_storage.filename:
        return None, "missing file"

    if not domain:
        return None, "missing domain"

    if not title or not title.strip():
        return None, "missing title"

    if not author or not author.strip():
        return None, "missing author"

    parsed_year = None
    if year:
        try:
            parsed_year = int(year)
        except (TypeError, ValueError):
            return None, "invalid year"

    book_id = _next_book_id(db)

    original_filename = Path(file_storage.filename).name
    safe_domain = domain.strip()
    stored_file_name = f"book_{book_id:03d}.pdf"

    target_dir = BOOKS_DIR / safe_domain
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / stored_file_name

    file_storage.save(target_path)

    book_title = title.strip()

    try:
        num_pages = get_pdf_page_count(target_path)
    except Exception:
        num_pages = None

    file_size_mb = round(target_path.stat().st_size / (1024 * 1024), 2)

    book_doc = {
        'book_id': book_id,
        'title': book_title,
        'author': author.strip(),
        'year': parsed_year,
        'domain': safe_domain,
        'file_name': original_filename,
        'stored_file_name': stored_file_name,
        'file_path': make_book_file_path(safe_domain, stored_file_name),
        'num_pages': num_pages,
        'file_size_mb': file_size_mb,
        'status': BOOK_STATUS_UPLOADED,
        'ingestion_method': None,
        'is_downloadable': True,
        'date_added': now_str(),
        'updated_at': now_str(),
    }

    books.insert_one(book_doc)
    return book_doc, None


def validate_process_book(book_id: int):
    db = get_database()
    books = db['books']

    book = books.find_one({'book_id': book_id})
    if not book:
        return None, "book not found"

    file_path = book.get('file_path')
    if not file_path:
        return None, "missing file_path"

    abs_path, _ = resolve_pdf_path(file_path)
    if abs_path is None or not abs_path.exists():
        return None, "file not found"

    return {'book_id': book_id, 'file_path': str(abs_path)}, None


def process_book(book_id: int):
    ensure_schema_indexes()
    db = get_database()
    books = db['books']
    pages = db['pages']

    validated, err = validate_process_book(book_id)
    if err:
        return None, err

    pdf_path = Path(validated['file_path'])

    doc = None
    try:
        doc = __import__('fitz').open(str(pdf_path))
        num_pages = len(doc)

        pages.delete_many({'book_id': book_id})
        pages_batch = []

        for page_num in range(num_pages):
            text = extract_page_text(doc, pdf_path, page_num)
            page_doc = build_page_document(book_id=book_id, page_number=page_num + 1, text_content=text)
            pages_batch.append(page_doc)

            if len(pages_batch) >= 100:
                pages.insert_many(pages_batch)
                pages_batch = []

        if pages_batch:
            pages.insert_many(pages_batch)

        books.update_one(
            {'book_id': book_id},
            {'$set': {'status': BOOK_STATUS_PROCESSED, 'num_pages': num_pages, 'updated_at': now_str()}},
        )

        return {
            'book_id': book_id,
            'num_pages': num_pages,
            'status': BOOK_STATUS_PROCESSED,
        }, None
    finally:
        if doc is not None:
            doc.close()


def process_uploaded_books():
    ensure_schema_indexes()
    db = get_database()
    books = db['books']

    uploaded = list(books.find({'status': BOOK_STATUS_UPLOADED}).sort('book_id', 1))
    if not uploaded:
        return {
            'processed_count': 0,
            'total_uploaded': 0,
            'processed_book_ids': [],
            'errors': [],
            'message': 'No uploaded books to process',
        }, None

    processed_ids: list[int] = []
    errors: list[dict] = []

    for book in uploaded:
        book_id = int(book.get('book_id'))
        try:
            result, err = process_book(book_id)
            if err:
                errors.append({'book_id': book_id, 'error': err})
                continue
            if result and result.get('book_id') is not None:
                processed_ids.append(int(result['book_id']))
        except Exception as exc:
            errors.append({'book_id': book_id, 'error': str(exc)})

    summary = f"Process completed ({len(processed_ids)}/{len(uploaded)})"
    if errors:
        summary = f"{summary} with {len(errors)} errors"

    return {
        'processed_count': len(processed_ids),
        'total_uploaded': len(uploaded),
        'processed_book_ids': processed_ids,
        'errors': errors,
        'message': summary,
    }, None


def build_index_and_update(full_rebuild: bool = False):
    ensure_schema_indexes()
    build_stats = build_index(full_rebuild=full_rebuild)

    db = get_database()
    books = db['books']

    updated_count = 0
    if not build_stats.get('skipped'):
        updated = books.update_many(
            {'status': BOOK_STATUS_PROCESSED},
            {'$set': {'status': BOOK_STATUS_INDEXED, 'updated_at': now_str()}},
        )
        updated_count = int(updated.modified_count)

    return {
        'status': BOOK_STATUS_INDEXED,
        'mode': build_stats.get('mode'),
        'indexed_books': build_stats.get('indexed_books', 0),
        'indexed_pages': build_stats.get('indexed_pages', 0),
        'empty_pages': build_stats.get('empty_pages', 0),
        'total_docs': build_stats.get('total_docs', 0),
        'unique_terms': build_stats.get('unique_terms', 0),
        'build_date': build_stats.get('build_date'),
        'full_rebuild': full_rebuild,
        'updated_books_status_count': updated_count,
        'skipped': bool(build_stats.get('skipped', False)),
        'message': build_stats.get('message'),
    }


def list_books(limit: int = 100):
    db = get_database()
    cursor = db['books'].find({}).sort('book_id', 1).limit(limit)
    return list(cursor)


def list_domains():
    if not BOOKS_DIR.exists():
        return []
    domains = [path.name for path in BOOKS_DIR.iterdir() if path.is_dir()]
    return sorted(domains)


def index_stats():
    idx_path = Path(SEARCH_INDEX_FILE)
    exists = idx_path.exists()
    size = idx_path.stat().st_size if exists else 0

    semantic_exists = all(
        path.exists() for path in (SEMANTIC_INDEX_FILE, SEMANTIC_META_FILE, SEMANTIC_PAGE_MAP_FILE)
    )
    semantic_size = 0
    if semantic_exists:
        semantic_size = sum(
            path.stat().st_size for path in (SEMANTIC_INDEX_FILE, SEMANTIC_META_FILE, SEMANTIC_PAGE_MAP_FILE)
        )

    build_date = None
    if exists:
        try:
            import pickle
            with open(idx_path, 'rb') as f:
                data = pickle.load(f)
                build_date = data.get('build_date')
        except Exception:
            build_date = None

    db = get_database()
    books = db['books']
    pages = db['pages']

    return {
        'index_available': exists,
        'index_size_bytes': size,
        'build_date': build_date,
        'semantic_index_available': semantic_exists,
        'semantic_index_size_bytes': semantic_size,
        'total_books': books.count_documents({}),
        'total_pages': pages.count_documents({}),
    }

