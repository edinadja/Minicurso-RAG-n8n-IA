"""
Python API do minicurso "RAG na Prática".

O n8n (orquestrador) chama esta API para executar as etapas de
processamento de documentos:

  POST /ingest  -> extrai texto, faz chunking, gera embeddings e
                    indexa os chunks no Qdrant.
  POST /search  -> gera o embedding da pergunta e busca os chunks
                    mais relevantes no Qdrant (contexto para o LLM).

A geração da resposta final (chamada ao LLM com o contexto recuperado)
é feita no próprio n8n, para deixar visível o papel de orquestrador.
"""

import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

from extraction import extract_text
from chunking import chunk_text
from embeddings import get_embedding, get_embedding_dimension
from vector_store import ensure_collection, upsert_chunks, search, collection_info

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))

app = FastAPI(
    title="RAG Minicurso - Python API",
    description="Etapas de processamento de documentos para o fluxo de RAG orquestrado pelo n8n.",
    version="1.0.0",
)


class SearchRequest(BaseModel):
    question: str
    top_k: int = 4


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/status")
def status():
    """Mostra quantos chunks já estão indexados no Qdrant. Útil para debug em aula."""
    return collection_info()


@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    """
    Recebe um arquivo (.txt, .md ou .pdf), executa:
      1) extração de texto
      2) chunking
      3) geração de embeddings
      4) indexação no Qdrant
    """
    content = await file.read()

    try:
        text = extract_text(file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not text.strip():
        raise HTTPException(status_code=400, detail="Não foi possível extrair texto do arquivo.")

    chunks = chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
    if not chunks:
        raise HTTPException(status_code=400, detail="O documento não gerou nenhum chunk.")

    embeddings = [get_embedding(chunk) for chunk in chunks]

    ensure_collection(vector_size=len(embeddings[0]))
    total = upsert_chunks(chunks, embeddings, source=file.filename)

    return {
        "filename": file.filename,
        "chunks_created": total,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
    }


@app.post("/search")
def search_endpoint(payload: SearchRequest):
    """
    Recebe uma pergunta, gera seu embedding e retorna os chunks mais
    similares encontrados no Qdrant. O n8n usa esses chunks como
    contexto para o prompt enviado ao LLM.
    """
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Campo 'question' vazio.")

    query_embedding = get_embedding(payload.question)
    results = search(query_embedding, top_k=payload.top_k)

    context = "\n\n---\n\n".join(r["text"] for r in results)

    return {
        "question": payload.question,
        "results": results,
        "context": context,
    }


@app.get("/embedding-dimension")
def embedding_dimension():
    """Endpoint auxiliar para debug: mostra a dimensão do vetor gerado."""
    return {"dimension": get_embedding_dimension()}
