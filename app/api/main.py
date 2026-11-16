import time

import requests
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import N8N_SYNC_WEBHOOK_URL, TOP_K
from app.drive_client import download_file, list_pdfs
from app.rag.indexer import index_pdf
from app.rag.qa import answer
from app.rag.vector_store import get_indexed_version


class PerguntaRequest(BaseModel):
    pergunta: str
    k: int = TOP_K


app = FastAPI(title="Assistente RAG Drive")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
def home():
    return FileResponse("app/static/index.html")


@app.get("/status")
def health():
    return {"status": "ok"}


@app.post("/indexar")
async def indexar(
    file: UploadFile = File(...),
    file_id: str = Form(...),
    file_name: str = Form(...),
    version: str = Form(""),
):
    file_bytes = await file.read()
    return index_pdf(file_bytes, file_id, file_name, version)


@app.get("/drive/arquivos")
def listar_arquivos_drive():
    arquivos = list_pdfs()
    for arquivo in arquivos:
        versao_atual = arquivo.get("modifiedTime", "")
        versao_indexada = get_indexed_version(arquivo["id"])
        arquivo["indexado"] = versao_indexada is not None
        arquivo["pendente"] = versao_indexada != versao_atual
    return {"arquivos": arquivos}


@app.post("/drive/indexar/{file_id}")
def indexar_arquivo_drive(file_id: str, force: bool = False):
    arquivos = {f["id"]: f for f in list_pdfs()}
    arquivo = arquivos.get(file_id)
    if not arquivo:
        return {"erro": "Arquivo não encontrado na pasta do Drive"}

    versao_atual = arquivo.get("modifiedTime", "")
    if not force and get_indexed_version(file_id) == versao_atual:
        return {"file_id": file_id, "status": "ja_atualizado", "chunks_criados": 0}

    file_bytes = download_file(file_id)
    return index_pdf(
        file_bytes,
        file_id=file_id,
        file_name=arquivo["name"],
        version=versao_atual,
    )


@app.post("/perguntar")
async def perguntar(request: PerguntaRequest):
    start = time.perf_counter()
    result = answer(request.pergunta, request.k)
    return {
        "resposta": result["resposta"],
        "fontes": result["fontes"],
        "tempo_segundos": round(time.perf_counter() - start, 2),
    }


@app.post("/sincronizar")
def sincronizar():
    try:
        response = requests.post(N8N_SYNC_WEBHOOK_URL, timeout=120)
        resultado = response.json() if response.content else None
        return {"status": "disparado", "codigo": response.status_code, "resultado": resultado}
    except requests.exceptions.RequestException as e:
        return {"status": "erro", "detalhe": str(e)}
