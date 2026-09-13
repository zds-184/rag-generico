"""API HTTP del RAG genérico (FastAPI).

Endpoints principales (Swagger en /docs):
  POST /query          -> respuesta en modo "rag" o "llm" con contextos, prompt, tiempos y uso de tokens
  POST /query/batch    -> varias preguntas en una llamada (útil para el evaluador)
  POST /retrieve       -> sólo recuperación (para métricas de retrieval)
  GET  /health         -> estado de Ollama, Qdrant y colección
  GET  /models         -> modelos disponibles en Ollama
  POST /models/pull    -> descargar otro modelo
  GET  /collection     -> info de la colección + manifest de la ingesta
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag.config import settings
from rag.pipeline import RAGPipeline

pipeline: RAGPipeline | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global pipeline
    pipeline = RAGPipeline(settings)
    yield


app = FastAPI(
    title="Generic RAG - MITRE ATT&CK",
    version="1.0.0",
    description="RAG genérico local (Ollama + Qdrant) sobre el corpus MITRE ATT&CK, con modo RAG y modo sólo LLM.",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ------------------------------------------------------------------ schemas
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, examples=["What is T1059.001 and how can it be mitigated?"])
    mode: Literal["rag", "llm"] = "rag"
    top_k: int | None = Field(None, ge=1, le=50)
    model: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    filters: dict[str, list[str]] | None = Field(
        None, examples=[{"object_type": ["technique", "sub-technique"], "domain": ["enterprise-attack"]}]
    )
    think: bool | None = None
    retrieval: Literal["hybrid", "dense", "sparse"] | None = Field(
        None, description="Estrategia de recuperación (por defecto RETRIEVAL_MODE del .env)"
    )
    include_prompt: bool = True


class BatchQueryRequest(BaseModel):
    items: list[QueryRequest] = Field(..., min_length=1, max_length=500)


class RetrieveRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int | None = Field(None, ge=1, le=100)
    filters: dict[str, list[str]] | None = None
    retrieval: Literal["hybrid", "dense", "sparse"] | None = None


class PullRequest(BaseModel):
    model: str


def _pipe() -> RAGPipeline:
    if pipeline is None:
        raise HTTPException(503, "pipeline no inicializado")
    return pipeline


# ---------------------------------------------------------------- endpoints
@app.get("/")
def root():
    return {"service": "generic-rag-mitre-attack", "docs": "/docs", "health": "/health"}


@app.get("/health")
async def health():
    return await run_in_threadpool(_pipe().health)


@app.get("/models")
async def models():
    p = _pipe()
    try:
        names = await run_in_threadpool(p.ollama.list_models)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(503, f"Ollama no disponible: {exc}") from exc
    return {"default": settings.llm_model, "embed_model": settings.embed_model, "models": names}


@app.post("/models/pull")
async def pull_model(req: PullRequest):
    try:
        return await run_in_threadpool(_pipe().ollama.pull, req.model)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"No se pudo descargar {req.model}: {exc}") from exc


@app.get("/collection")
async def collection():
    p = _pipe()
    info = await run_in_threadpool(p.store.info)
    manifest_path = Path(settings.data_dir) / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
    return {"collection": info, "manifest": manifest}


@app.post("/retrieve")
async def retrieve(req: RetrieveRequest):
    try:
        contexts = await run_in_threadpool(_pipe().retrieve, req.question, req.top_k, req.filters, req.retrieval)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, str(exc)) from exc
    return {"question": req.question, "retrieval": req.retrieval or settings.retrieval_mode, "contexts": contexts}


@app.post("/query")
async def query(req: QueryRequest):
    try:
        return await run_in_threadpool(_pipe().query, **req.model_dump())
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, str(exc)) from exc


@app.post("/query/batch")
async def query_batch(req: BatchQueryRequest):
    results = []
    for item in req.items:
        try:
            results.append(await run_in_threadpool(_pipe().query, **item.model_dump()))
        except Exception as exc:  # noqa: BLE001
            results.append({"question": item.question, "mode": item.mode, "error": str(exc)})
    return {"results": results}
