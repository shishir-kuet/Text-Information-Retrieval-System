from io import BytesIO

from flask import Blueprint, request, send_file

from app.services.library_service import (
    get_book,
    get_book_pdf_path,
    get_page,
    get_page_pdf_bytes,
    get_page_text,
    list_books,
    list_pages,
    process_book,
    upload_book,
)
from app.utils.api_response import error, success


bp = Blueprint("library", __name__, url_prefix="/api/library")


def _serialize(doc: dict):
    out = dict(doc)
    out.pop("_id", None)
    return out


@bp.post("/books/upload")
def upload():
    file_storage = request.files.get("file")
    title = (request.form.get("title") or "").strip()
    author = (request.form.get("author") or "").strip()
    year = (request.form.get("year") or "").strip() or None

    book_doc, err = upload_book(file_storage, title, author, year)
    if err == "missing file":
        return error("file is required", status=400)
    if err == "missing title":
        return error("title is required", status=400)
    if err == "invalid year":
        return error("year must be a number", status=400)
    if err:
        return error(err, status=400)

    return success(_serialize(book_doc), status=201)


@bp.post("/books/<int:book_id>/process")
def process(book_id: int):
    result, err = process_book(book_id)
    if err:
        return error(err, status=400)
    return success(result)


@bp.get("/books")
def books_route():
    limit = request.args.get("limit", 200)
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        return error("limit must be an integer", status=400)

    if limit <= 0 or limit > 500:
        return error("limit must be between 1 and 500", status=400)

    items = list_books(limit=limit)
    return success({"count": len(items), "items": [_serialize(item) for item in items]})


@bp.get("/books/<int:book_id>")
def book_detail(book_id: int):
    book = get_book(book_id)
    if not book:
        return error("book not found", status=404)
    return success(_serialize(book))


@bp.get("/books/<int:book_id>/pages")
def book_pages(book_id: int):
    items = list_pages(book_id)
    return success({"count": len(items), "items": [_serialize(item) for item in items]})


@bp.get("/pages/<page_id>")
def page_detail(page_id: str):
    page = get_page(page_id)
    if not page:
        return error("page not found", status=404)
    return success(_serialize(page))


@bp.get("/pages/<page_id>/text")
def page_text(page_id: str):
    text = get_page_text(page_id)
    if text is None:
        return error("page not found", status=404)
    return success({"page_id": page_id, "text_content": text})


@bp.get("/pages/<page_id>/pdf")
def page_pdf(page_id: str):
    pdf_bytes, filename = get_page_pdf_bytes(page_id)
    if pdf_bytes is None:
        return error("page not found", status=404)
    return send_file(BytesIO(pdf_bytes), as_attachment=False, download_name=filename, mimetype="application/pdf", conditional=False)


@bp.get("/books/<int:book_id>/download")
def book_download(book_id: int):
    path = get_book_pdf_path(book_id)
    if not path:
        return error("book not found", status=404)
    book = get_book(book_id) or {}
    filename = book.get("file_name") or f"book_{book_id:03d}.pdf"
    return send_file(path, as_attachment=True, download_name=filename, mimetype="application/pdf", conditional=False)
