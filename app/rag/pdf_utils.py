import io

from pypdf import PdfReader


def extract_pages(file_bytes: bytes) -> list[dict]:
    """Retorna lista de {'page': int, 'text': str}, uma entrada por página."""
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({"page": i, "text": text})
    return pages
