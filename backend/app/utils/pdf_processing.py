from pathlib import Path

import fitz
import pytesseract
from pdf2image import convert_from_path

from backend.app.config.settings import settings


TESSERACT_PATH = settings.tesseract_path

try:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False


def extract_text_normal(page) -> str:
    return str(page.get_text())


def extract_text_ocr(pdf_path: Path, page_num: int) -> str:
    try:
        images = convert_from_path(
            str(pdf_path),
            first_page=page_num + 1,
            last_page=page_num + 1,
            dpi=200,
        )
        if images:
            return pytesseract.image_to_string(images[0])
        return ""
    except Exception:
        return ""


def extract_page_text(doc, pdf_path: Path, page_num: int) -> str:
    page = doc[page_num]
    text = extract_text_normal(page)
    if len(text.strip()) < 50 and OCR_AVAILABLE:
        text = extract_text_ocr(pdf_path, page_num)
    return text


def get_pdf_page_count(pdf_path: Path) -> int:
    doc = fitz.open(str(pdf_path))
    count = len(doc)
    doc.close()
    return count
