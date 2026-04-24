from pathlib import Path

from app.config.paths import BOOKS_DIR


def resolve_pdf_path(raw_file_path: str | None):
    if not raw_file_path:
        return None, None

    normalized = str(raw_file_path).replace("\\", "/")
    path_obj = Path(normalized)
    if path_obj.is_absolute():
        abs_path = path_obj
        pdf_url = None
        try:
            rel = abs_path.resolve().relative_to(BOOKS_DIR.resolve())
            pdf_url = f"backend-library/books/{rel.as_posix()}".replace("//", "/")
        except Exception:
            pdf_url = None
        return abs_path, pdf_url

    if normalized.startswith("backend-library/books/"):
        relative = normalized[len("backend-library/books/") :]
    elif normalized.startswith("books/"):
        relative = normalized[len("books/") :]
    else:
        relative = normalized

    absolute_path = BOOKS_DIR / relative
    pdf_url = f"backend-library/books/{relative}".replace("//", "/")
    return absolute_path, pdf_url


def make_book_file_path(stored_file_name: str) -> str:
    safe_name = Path(stored_file_name).name
    return f"backend-library/books/{safe_name}".replace("//", "/")
