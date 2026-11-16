CHARS_PER_TOKEN = 4
MIN_TOKENS = 300
MAX_TOKENS = 800
OVERLAP_TOKENS = 50

MIN_CHARS = MIN_TOKENS * CHARS_PER_TOKEN
MAX_CHARS = MAX_TOKENS * CHARS_PER_TOKEN
OVERLAP_CHARS = OVERLAP_TOKENS * CHARS_PER_TOKEN


def chunk_pages(pages: list[dict]) -> list[dict]:
    """Recebe [{'page': int, 'text': str}, ...] e retorna
    [{'text': str, 'page': int}, ...] com chunks de MIN..MAX_CHARS e overlap.
    Um chunk nunca mistura texto de páginas diferentes, então pode ficar
    menor que MIN_CHARS perto do fim de uma página.
    """
    chunks = []
    for page_data in pages:
        page_num = page_data["page"]
        text = page_data["text"]
        start = 0
        length = len(text)
        while start < length:
            end = min(start + MAX_CHARS, length)
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({"text": chunk_text, "page": page_num})
            if end >= length:
                break
            start = end - OVERLAP_CHARS
    return chunks
