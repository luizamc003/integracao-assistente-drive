from sentence_transformers import SentenceTransformer

from app.config import EMBEDDING_MODEL

_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_model()
    return model.encode(texts).tolist()
