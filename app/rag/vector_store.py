import chromadb

from app.config import CHROMA_PERSIST_DIR

_client = None
_collection = None

COLLECTION_NAME = "documentos"


def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        _collection = _client.get_or_create_collection(COLLECTION_NAME)
    return _collection


def delete_file_chunks(file_id: str):
    collection = get_collection()
    collection.delete(where={"file_id": file_id})


def add_chunks(file_id: str, ids: list[str], texts: list[str], embeddings: list[list[float]], metadatas: list[dict]):
    collection = get_collection()
    collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)


def query(embedding: list[float], k: int):
    collection = get_collection()
    return collection.query(query_embeddings=[embedding], n_results=k)


def get_indexed_version(file_id: str) -> str | None:
    collection = get_collection()
    result = collection.get(where={"file_id": file_id}, limit=1)
    if not result["metadatas"]:
        return None
    return result["metadatas"][0].get("version")
