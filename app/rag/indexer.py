import time
from datetime import datetime, timezone

from app.rag.chunking import chunk_pages
from app.rag.embeddings import embed_texts
from app.rag.pdf_utils import extract_pages
from app.rag.vector_store import add_chunks, delete_file_chunks


def index_pdf(file_bytes: bytes, file_id: str, file_name: str, version: str = "") -> dict:
    start = time.perf_counter()

    pages = extract_pages(file_bytes)
    chunks = chunk_pages(pages)

    if not chunks:
        return {"file_id": file_id, "chunks_criados": 0, "tempo_segundos": round(time.perf_counter() - start, 2)}

    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)

    indexed_at = datetime.now(timezone.utc).isoformat()
    ids = [f"{file_id}_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "file_id": file_id,
            "file_name": file_name,
            "page": c["page"],
            "version": version,
            "indexed_at": indexed_at,
        }
        for c in chunks
    ]

    delete_file_chunks(file_id)
    add_chunks(file_id, ids, texts, embeddings, metadatas)

    return {
        "file_id": file_id,
        "chunks_criados": len(chunks),
        "tempo_segundos": round(time.perf_counter() - start, 2),
    }
