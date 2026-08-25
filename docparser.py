# ------------------------------------------------------------------
# DocMaster AI -- document parsing (architecture box 2: "Parsing")
# pypdf + pdfplumber for born-digital PDFs; Tesseract OCR fallback
# for scanned pages (only if the tesseract binary is installed).
# ------------------------------------------------------------------
import io

def extract_pages(pdf_bytes: bytes) -> list[str]:
    """Return a list of page texts, one string per page, in order."""
    pages = _with_pdfplumber(pdf_bytes)
    if not pages:
        pages = _with_pypdf(pdf_bytes)
    pages = [p or "" for p in pages]
    # OCR fallback for pages that yielded (almost) no text
    for i, txt in enumerate(pages):
        if len(txt.strip()) < 20:
            ocr = _ocr_page(pdf_bytes, i)
            if ocr:
                pages[i] = ocr
    return pages


def _with_pdfplumber(pdf_bytes: bytes) -> list[str]:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            return [page.extract_text() or "" for page in pdf.pages]
    except Exception:
        return []


def _with_pypdf(pdf_bytes: bytes) -> list[str]:
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        return [page.extract_text() or "" for page in reader.pages]
    except Exception:
        return []


def ocr_available() -> bool:
    """True only if pytesseract AND the tesseract binary AND pdf2image deps exist."""
    try:
        import shutil
        import pytesseract  # noqa: F401
        return shutil.which("tesseract") is not None
    except Exception:
        return False


def _ocr_page(pdf_bytes: bytes, page_index: int) -> str:
    """OCR a single page; returns '' when OCR is not installed (graceful skip)."""
    if not ocr_available():
        return ""
    try:
        import pypdfium2 as pdfium  # lightweight PDF rasteriser
        import pytesseract
        pdf = pdfium.PdfDocument(pdf_bytes)
        if page_index >= len(pdf):
            return ""
        bitmap = pdf[page_index].render(scale=2.5)
        img = bitmap.to_pil()
        return pytesseract.image_to_string(img) or ""
    except Exception:
        return ""
