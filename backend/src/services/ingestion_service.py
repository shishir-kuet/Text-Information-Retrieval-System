"""Ingestion service: extract text from PDFs and store in MongoDB."""

import os
from datetime import datetime
from pathlib import Path

import re

import fitz  # PyMuPDF

from backend.src.utils.logger import get_logger

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
MIN_TEXT_LENGTH = 50  # Characters below which OCR is attempted


_ROMAN_RE = re.compile(
    r'^(m{0,4}(?:cm|cd|d?c{0,3})(?:xc|xl|l?x{0,3})(?:ix|iv|v?i{0,3}))$',
    re.IGNORECASE,
)


def _roman_to_int(s: str) -> int:
    vals = {'i': 1, 'v': 5, 'x': 10, 'l': 50, 'c': 100, 'd': 500, 'm': 1000}
    s = s.lower()
    total = 0
    for idx, ch in enumerate(s):
        cur = vals.get(ch, 0)
        nxt = vals.get(s[idx + 1], 0) if idx + 1 < len(s) else 0
        total += -cur if cur < nxt else cur
    return total


def _is_roman(token: str) -> bool:
    """Return True if *token* is a non-empty valid Roman numeral with value 1-999."""
    if not token or not _ROMAN_RE.match(token):
        return False
    return 1 <= _roman_to_int(token) <= 999


def _extract_page_num_from_text(text: str):
    """Extract the visible page number from a page's running header or footer.

    Checks (in order):
    1. First line is entirely a number or Roman numeral.
    2. First line starts with number/Roman + word  (e.g. "2 CHAPTER 1 …").
    3. First line ends with word + number/Roman    (e.g. "CONTENTS ix").
    4. Last line is entirely a number              (chapter opener, page at bottom).

    Returns the page-label string, or None if not found.
    """
    if not text:
        return None
    lines = text.strip().split('\n')
    first = lines[0].strip() if lines else ''
    last  = lines[-1].strip() if lines else ''

    # 1. First line IS the page number
    if re.fullmatch(r'\d+', first):
        return first
    if _is_roman(first):
        return first.lower()

    # 2a. Leading Arabic number: "2 CHAPTER 1…"  (dot after digit = section ref, skip)
    m = re.match(r'^(\d+)\s+\S', first)
    if m:
        return m.group(1)

    # 2b. Leading Roman numeral: "xxii PREFACE"
    m = re.match(
        r'^(m{0,4}(?:cm|cd|d?c{0,3})(?:xc|xl|l?x{0,3})(?:ix|iv|v?i{0,3}))\s+\S',
        first, re.IGNORECASE,
    )
    if m and _is_roman(m.group(1)):
        return m.group(1).lower()

    # 3a. Trailing Arabic number: "CONTENTS 5" or "WHAT IS AN ALGORITHM? 3"
    m = re.search(r'(?<=\s)(\d+)$', first)
    if m:
        return m.group(1)

    # 3b. Trailing Roman numeral: "CONTENTS ix"
    m = re.search(
        r'(?<=\s)(m{0,4}(?:cm|cd|d?c{0,3})(?:xc|xl|l?x{0,3})(?:ix|iv|v?i{0,3}))$',
        first, re.IGNORECASE,
    )
    if m and _is_roman(m.group(1)):
        return m.group(1).lower()

    # 4. Last line is a Roman numeral (e.g. footer on a PREFACE page).
    #    Skip this heuristic for TOC / Index pages, whose last line may be a
    #    Roman-numeral page-reference entry rather than the page's own number.
    _toc_header = re.compile(r'^(contents?|table\s+of\s+contents|index)\s*$', re.IGNORECASE)
    if not _toc_header.match(first) and _is_roman(last):
        return last.lower()

    return None


def _get_display_page_number(doc, page_num: int, text: str = '') -> str:
    """Return the display page label.

    Priority:
    1. Valid embedded PDF page label (from the PageLabels dictionary).
    2. Page number visible in the OCR/embedded text (running header/footer).
    3. Physical 1-based page position as a fallback.
    """
    raw = doc[page_num].get_label()
    # Valid PDF label — use it directly.
    if raw and not (raw.startswith('<') and raw.endswith('>')):
        return raw
    # No valid PDF label: try to read the printed number from the page text.
    extracted = _extract_page_num_from_text(text)
    if extracted:
        return extracted
    return str(page_num + 1)


def _setup_tesseract(use_ocr: bool) -> bool:
    """Configure Tesseract and return whether OCR is usable."""
    if not use_ocr:
        return False
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        return True
    except Exception:
        return False


def extract_text_normal(page) -> str:
    """Extract embedded text from a PDF page using PyMuPDF."""
    return str(page.get_text())


def extract_text_ocr(pdf_path: Path, page_num: int) -> str:
    """Rasterise a PDF page with PyMuPDF and run Tesseract OCR on it.

    Uses fitz (PyMuPDF) for rendering — no poppler / pdf2image dependency needed.
    Renders at 300 DPI (matrix scale = 300/72 ≈ 4.17) for good OCR accuracy.
    """
    try:
        import pytesseract
        from PIL import Image
        import io

        doc_ocr = fitz.open(str(pdf_path))
        page = doc_ocr[page_num]
        # 300 DPI: scale factor = 300 / 72
        mat = fitz.Matrix(300 / 72, 300 / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        doc_ocr.close()

        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img)
    except Exception as e:
        get_logger(__name__).warning(f"OCR error on {pdf_path.name} p{page_num+1}: {e}")
        return ""


def extract_page_text(doc, pdf_path: Path, page_num: int, use_ocr: bool) -> str:
    """Try normal extraction first; fall back to OCR if text is too short."""
    text = extract_text_normal(doc[page_num])
    if len(text.strip()) < MIN_TEXT_LENGTH and use_ocr:
        text = extract_text_ocr(pdf_path, page_num)
    return text


def ingest_books(db, books_folder: Path, use_ocr: bool = True,
                 clear_existing: bool = False) -> dict:
    """
    Scan *books_folder* for domain sub-folders containing PDFs, extract their
    text, and store everything in MongoDB.

    Parameters
    ----------
    db           : active pymongo Database instance
    books_folder : root folder that contains domain sub-folders (e.g. History/)
    use_ocr      : whether to fall back to Tesseract for image-only pages
    clear_existing : if True, wipe books/pages collections first
                     (requires explicit opt-in — default False to protect data)

    Returns
    -------
    dict with totals: {books, pages}
    """
    logger = get_logger(__name__)
    books_col = db["books"]
    pages_col = db["pages"]

    if clear_existing:
        logger.warning("Clearing existing data from books and pages collections.")
        books_col.delete_many({})
        pages_col.delete_many({})

    ocr_available = _setup_tesseract(use_ocr)
    if not ocr_available:
        logger.warning("OCR disabled — scanned PDFs will have empty text.")

    books_folder = Path(books_folder)
    if not books_folder.exists():
        raise FileNotFoundError(f"Books folder not found: {books_folder}")

    domain_folders = sorted(f for f in books_folder.iterdir() if f.is_dir())
    if not domain_folders:
        raise ValueError(f"No domain sub-folders found in {books_folder}")

    # Determine next available book_id to support incremental ingestion
    last = books_col.find_one(sort=[("book_id", -1)])
    book_id = (last["book_id"] + 1) if last else 1

    total_books = 0
    total_pages = 0

    for domain_folder in domain_folders:
        domain = domain_folder.name
        pdf_files = sorted(domain_folder.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDFs in {domain}/")
            continue

        logger.info(f"[DOMAIN] {domain.upper()} — {len(pdf_files)} book(s)")

        for pdf_path in pdf_files:
            try:
                logger.info(f"  Processing: {pdf_path.name}")
                doc = fitz.open(str(pdf_path))
                num_pages = len(doc)
                title = pdf_path.stem
                file_size_mb = round(os.path.getsize(pdf_path) / (1024 * 1024), 2)

                book_doc = {
                    "book_id": book_id,
                    "title": title,
                    "domain": domain,
                    "file_path": str(pdf_path),
                    "num_pages": num_pages,
                    "file_size_mb": file_size_mb,
                    "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                books_col.insert_one(book_doc)

                pages_batch = []
                for page_num in range(num_pages):
                    text = extract_page_text(doc, pdf_path, page_num, ocr_available)
                    pages_batch.append({
                        "page_id": f"{book_id}_{page_num + 1}",
                        "book_id": book_id,
                        "page_number": page_num + 1,
                        "display_page_number": _get_display_page_number(doc, page_num, text),
                        "text_content": text,
                        "word_count": len(text.split()),
                        "char_count": len(text),
                    })
                    if len(pages_batch) >= 100:
                        pages_col.insert_many(pages_batch)
                        pages_batch = []
                    if (page_num + 1) % 100 == 0:
                        logger.info(f"    {page_num + 1}/{num_pages} pages...")

                if pages_batch:
                    pages_col.insert_many(pages_batch)
                doc.close()

                logger.info(f"  [OK] {num_pages} pages ({file_size_mb} MB), book_id={book_id}")
                total_books += 1
                total_pages += num_pages
                book_id += 1

            except Exception as exc:
                logger.error(f"  [ERR] {pdf_path.name}: {exc}")

    logger.info(f"Ingestion complete: {total_books} books, {total_pages} pages.")
    return {"books": total_books, "pages": total_pages}
