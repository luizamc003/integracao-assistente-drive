# Assistente RAG com Google Drive, n8n e FastAPI

Sistema de perguntas e respostas sobre documentos PDF armazenados no Google Drive. A indexação é disparada pelo n8n sempre que a pasta do Drive muda; as perguntas são respondidas com base apenas nos trechos recuperados, sempre citando a fonte (arquivo e página).
Projeto roda localmente. 

Tecnologias e principais conceitos:
RAG · Retrieval-Augmented Generation · Google Drive · n8n · FastAPI · DeepSeek · LLM · embeddings · ChromaDB · banco vetorial · busca semântica · webhook · automação · indexação de documentos · PDF · citação de fontes · Python

###Apresentação

<img width="1483" height="937" alt="image" src="https://github.com/user-attachments/assets/5c5560eb-e689-4b21-8cbe-977270e5505c" />


## Arquitetura

```
Google Drive (pasta de PDFs)
        │
        ▼
      n8n  ──(webhook)──►  FastAPI
        │                     │
   lista arquivos        extrai texto (pypdf)
   da pasta               divide em chunks
        │                 gera embeddings (sentence-transformers)
        ▼                 salva no Chroma (banco vetorial)
  chama /drive/indexar/{id}
  para cada arquivo pendente


      Interface web (app/static/index.html)
        │
        ▼
  POST /perguntar ──► embedding da pergunta ──► busca top-k no Chroma
                                                      │
                                      sem trecho relevante? recusa, sem chamar o LLM
                                                      │
                                              monta prompt com citação obrigatória
                                                      │
                                              chama o DeepSeek (temperature=0)
                                                      │
                                              resposta + fontes (arquivo, página)
```

## Estrutura do projeto

```
app/
  config.py            variáveis de ambiente (.env)
  drive_client.py       integração com Google Drive (conta de serviço)
  api/
    main.py             FastAPI: endpoints e interface web
  rag/
    pdf_utils.py         extração de texto por página
    chunking.py          divisão em chunks (300-800 tokens, overlap)
    embeddings.py         geração de embeddings (modelo multilíngue)
    vector_store.py       Chroma (banco vetorial persistente)
    indexer.py            orquestra extração → chunking → embedding → indexação
    deepseek_client.py     chamada ao DeepSeek (SDK compatível OpenAI)
    qa.py                  recuperação + limiar de similaridade + prompt + resposta
  static/
    index.html            interface web simples
eval/
  perguntas.json          conjunto de avaliação (20 perguntas)
  run_eval.py             script de avaliação (compara k=3 vs k=5)
  resultado_k3.json        resultados detalhados k=3
  resultado_k5.json        resultados detalhados k=5
credentials.json          chave da conta de serviço Google (não versionado)
.env                       variáveis de ambiente (não versionado)
```

## Configuração

### 1. Ambiente Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Google Drive

- Crie uma pasta no Drive com os PDFs a indexar.
- Crie uma conta de serviço no Google Cloud com permissão de **leitura apenas nessa pasta** (compartilhe a pasta com o e-mail da conta de serviço).
- Baixe a chave JSON da conta de serviço e salve como `credentials.json` na raiz do projeto.

### 3. Variáveis de ambiente (`.env`)

```
DEEPSEEK_API_KEY=sua_chave_aqui
DEEPSEEK_BASE_URL=https://api.deepseek.com
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
CHROMA_PERSIST_DIR=./chroma_db
GOOGLE_SERVICE_ACCOUNT_FILE=./credentials.json
GOOGLE_DRIVE_FOLDER_ID=id_da_pasta_do_drive
TOP_K=4
MAX_DISTANCE=22
N8N_SYNC_WEBHOOK_URL=http://localhost:5678/webhook/assistente_drive
```

### 4. n8n

Fluxo: **Webhook → Google Drive (Search, pasta por ID, filtro mimeType=application/pdf) → HTTP Request (`POST http://<IP>:8000/drive/indexar/{{ $json.id }}`)**.

- Se o n8n rodar em container Docker e a API na máquina host, use o IP da bridge do Docker (`172.17.0.1` por padrão) em vez de `localhost`, e libere a porta no firewall para a rede do container:
  ```bash
  sudo ufw allow from 172.17.0.0/16 to any port 8000
  ```
- Ative **"Continue On Fail"** no nó HTTP Request para que a falha de 1 arquivo não interrompa o processamento dos demais.
- O endpoint `/drive/indexar/{id}` já verifica a versão (`modifiedTime`) e pula arquivos sem mudança — não é necessário filtrar isso no n8n.
- Ative o workflow ("Active") para usar a Production URL do webhook.

<img width="852" height="261" alt="image" src="https://github.com/user-attachments/assets/77e8a242-cd43-409f-9228-51190d68a89b" />


## Executando

```bash
source venv/bin/activate
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Abra `http://localhost:8000/` para a interface web, ou `http://localhost:8000/docs` para a documentação automática (Swagger).

## Endpoints

| Endpoint | Método | Descrição |
|---|---|---|
| `/` | GET | Interface web |
| `/status` | GET | Health check |
| `/indexar` | POST | Indexa um PDF enviado via upload (multipart) |
| `/drive/arquivos` | GET | Lista os PDFs da pasta do Drive, com status `indexado`/`pendente` |
| `/drive/indexar/{file_id}` | POST | Baixa e indexa um arquivo do Drive (pula se já atualizado; `?force=true` força reindexação) |
| `/perguntar` | POST | `{"pergunta": "...", "k": 4}` → resposta com citações |
| `/sincronizar` | POST | Dispara o webhook do n8n e repassa o resultado |

## Como a indexação evita duplicação

Cada chunk é salvo com o `file_id` do Drive como metadado. Antes de inserir os novos chunks de um arquivo, todos os chunks antigos com aquele `file_id` são apagados. Isso cobre atualizações feitas via "Manage versions" no Drive (mesmo ID, conteúdo novo).

**Limitação conhecida:** se um arquivo for apagado e reenviado ao Drive (em vez de atualizado), ele recebe um novo `file_id`, e a versão antiga permanece órfã no banco vetorial até ser removida manualmente. Não há hoje uma rotina automática de limpeza de arquivos removidos da pasta.

## Avaliação

Rodar com:

```bash
python3 eval/run_eval.py
```

Resultado obtido com 20 perguntas (16 respondíveis sobre 13 documentos, 4 fora do domínio):

| k | Recall (doc certo no top-k) | Recusas indevidas | Recusa correta (fora do domínio) | Tempo médio/pergunta |
|---|---|---|---|---|
| 3 | 73.3% | 6 de 16 | 100% | 1.6s |
| 5 | 80.0% | 8 de 16 | 100% | 1.45s |

**Observações:**
- k=5 recupera o documento certo com mais frequência, mas em alguns casos o contexto adicional faz o modelo ser mais conservador e recusar respostas que, com k=3, ele teria dado — o aumento de k nem sempre melhora a resposta final, mesmo melhorando o recall.
- A recusa de perguntas fora do domínio foi 100% correta em ambas as configurações, sem nenhuma chamada ao LLM nesses casos (filtro por distância de similaridade).
- Custo por pergunta não foi medido diretamente neste script (não há tracking de tokens da resposta do DeepSeek); é um próximo passo natural.

## Próximos passos

- Adicionar tracking de tokens/custo por chamada ao DeepSeek.
- Rotina de limpeza de arquivos removidos do Drive (comparar IDs indexados com os atualmente presentes na pasta).
- Agregar os resultados de todos os arquivos processados pelo n8n numa única resposta do webhook (hoje o modo "When Last Node Finishes" retorna só o resultado do último item processado).
