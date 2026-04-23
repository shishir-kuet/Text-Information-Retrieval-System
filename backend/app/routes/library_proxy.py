from flask import Blueprint

from backend.app.services.library_client import LibraryClient
from backend.app.utils.api_response import error, success

bp = Blueprint("library_proxy", __name__, url_prefix="/api/library")
client = LibraryClient()


@bp.get("/books")
def books():
    try:
        return success(client.list_books())
    except Exception as exc:
        return error(str(exc) or "request failed", status=502)


@bp.get("/books/<int:book_id>")
def book_detail(book_id: int):
    try:
        return success(client.get_book(book_id))
    except Exception as exc:
        return error(str(exc) or "request failed", status=502)


@bp.get("/books/<int:book_id>/pages")
def book_pages(book_id: int):
    try:
        return success(client.list_pages(book_id))
    except Exception as exc:
        return error(str(exc) or "request failed", status=502)


@bp.get("/pages/<page_id>")
def page_detail(page_id: str):
    try:
        return success(client.get_page(page_id))
    except Exception as exc:
        return error(str(exc) or "request failed", status=502)


@bp.get("/pages/<page_id>/text")
def page_text(page_id: str):
    try:
        return success(client.get_page_text(page_id))
    except Exception as exc:
        return error(str(exc) or "request failed", status=502)
