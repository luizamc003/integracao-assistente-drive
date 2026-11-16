from app.config import MAX_DISTANCE, TOP_K
from app.rag.deepseek_client import ask
from app.rag.embeddings import embed_texts
from app.rag.vector_store import query

PROMPT_TEMPLATE = """Responda a pergunta usando APENAS as informações dos trechos abaixo. \
Para cada afirmação da sua resposta, cite a fonte entre parênteses no formato (arquivo, página). \
Se os trechos não tiverem informação suficiente para responder, diga que não encontrou a resposta nos documentos.

Trechos:
{trechos}

Pergunta: {pergunta}

Resposta:"""


def retrieve(pergunta: str, k: int = TOP_K):
    embedding = embed_texts([pergunta])[0]
    result = query(embedding, k)

    documents = result["documents"][0]
    metadatas = result["metadatas"][0]
    distances = result["distances"][0]

    hits = [
        {"text": doc, "metadata": meta, "distance": dist}
        for doc, meta, dist in zip(documents, metadatas, distances)
        if dist <= MAX_DISTANCE
    ]
    return hits


def build_prompt(pergunta: str, hits: list[dict]) -> str:
    trechos = "\n\n".join(
        f"[{h['metadata']['file_name']}, página {h['metadata']['page']}]\n{h['text']}"
        for h in hits
    )
    return PROMPT_TEMPLATE.format(trechos=trechos, pergunta=pergunta)


def answer(pergunta: str, k: int = TOP_K) -> dict:
    hits = retrieve(pergunta, k)

    if not hits:
        return {
            "resposta": "Não encontrei essa informação nos documentos.",
            "fontes": [],
        }

    prompt = build_prompt(pergunta, hits)
    resposta = ask(prompt)

    fontes = [
        {"arquivo": h["metadata"]["file_name"], "pagina": h["metadata"]["page"]}
        for h in hits
    ]

    return {"resposta": resposta, "fontes": fontes}
