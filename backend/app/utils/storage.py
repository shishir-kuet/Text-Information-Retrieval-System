from pathlib import Path

from backend.app.config.paths import BOOKS_DIR


def resolve_pdf_path(raw_file_path: str | None):
    """Resolve a stored book file_path into (absolute_path, pdf_url)."""
    if not raw_file_path:
        return None, None

    normalized = str(raw_file_path).replace("\\", "/")

    # Absolute path case
    path_obj = Path(normalized)
    if path_obj.is_absolute():
        abs_path = path_obj
        pdf_url = None
        try:
            rel = abs_path.resolve().relative_to(BOOKS_DIR.resolve())
            pdf_url = f"backend/books/{rel.as_posix()}".replace("//", "/")
        except Exception:
            pdf_url = None
        return abs_path, pdf_url

    # Relative path cases
    if normalized.startswith("backend/books/"):
        relative = normalized[len("backend/books/") :]
    elif normalized.startswith("books/"):
        relative = normalized[len("books/") :]
    else:
        relative = normalized

    absolute_path = BOOKS_DIR / relative
    pdf_url = f"backend/books/{relative}".replace("//", "/")
    return absolute_path, pdf_url


def make_book_file_path(domain: str, stored_file_name: str) -> str:
    safe_domain = (domain or "").strip()
    safe_name = Path(stored_file_name).name
    return f"backend/books/{safe_domain}/{safe_name}".replace("//", "/")
