"""Pipeline RAG genérico: retrieve -> build prompt -> generate. Modo `llm` omite el retrieval."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Literal

from . import prompts
from .config import Settings
from .embeddings import Embedder
from .ollama_client import OllamaClient
from .sparse import query_sparse_vector
from .vectorstore import VectorStore

Mode = Literal["rag", "llm"]


class RAGPipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.ollama = OllamaClient(settings.ollama_url, timeout=settings.request_timeout)
        self.embedder = Embedder(
            self.ollama,
            settings.embed_model,
            settings.embed_batch_size,
            settings.embed_doc_prefix,
            settings.embed_query_prefix,
        )
        self.store = VectorStore(settings.qdrant_url, settings.collection, settings.qdrant_api_key)

    # -------------------------------------------------------------- retrieval
    def retrieve(
        self,
        question: str,
        top_k: int | None = None,
        filters: dict | None = None,
        retrieval: str | None = None,
    ) -> list[dict]:
        mode = retrieval or self.settings.retrieval_mode
        dense = self.embedder.embed_query(question) if mode in ("dense", "hybrid") else None
        sparse = query_sparse_vector(question) if mode in ("sparse", "hybrid") else None
        hits = self.store.search(dense, sparse, top_k or self.settings.top_k, mode=mode, filters=filters)
        contexts = []
        for rank, h in enumerate(hits, start=1):
            payload = dict(h["payload"])
            text = payload.pop("text", "")
            contexts.append({"rank": rank, "score": h["score"], "point_id": h["id"], "text": text, "metadata": payload})
        return contexts

    # ---------------------------------------------------------------- prompts
    @staticmethod
    def format_context(contexts: list[dict]) -> str:
        items = []
        for c in contexts:
            m = c["metadata"]
            source = " - ".join(x for x in (m.get("attack_id"), m.get("name")) if x) or m.get("doc_id", "unknown")
            items.append(prompts.CONTEXT_ITEM_TEMPLATE.format(rank=c["rank"], source=source, text=c["text"]))
        return "\n\n".join(items)

    def build_messages(self, question: str, mode: Mode, contexts: list[dict]) -> list[dict]:
        if mode == "rag":
            system = prompts.RAG_SYSTEM
            user = prompts.RAG_USER_TEMPLATE.format(context=self.format_context(contexts), question=question)
        else:
            system = prompts.LLM_SYSTEM
            user = prompts.LLM_USER_TEMPLATE.format(question=question)
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]

    # ------------------------------------------------------------------ query
    def query(
        self,
        question: str,
        mode: Mode = "rag",
        top_k: int | None = None,
        model: str | None = None,
        temperature: float | None = None,
        filters: dict | None = None,
        think: bool | None = None,
        retrieval: str | None = None,
        include_prompt: bool = True,
    ) -> dict:
        s = self.settings
        model = model or s.llm_model
        temperature = s.temperature if temperature is None else temperature
        think = s.llm_think if think is None else think
        top_k = top_k or s.top_k
        retrieval = retrieval or s.retrieval_mode

        t0 = time.perf_counter()
        contexts: list[dict] = []
        if mode == "rag":
            contexts = self.retrieve(question, top_k, filters, retrieval)
        t_retrieval = (time.perf_counter() - t0) * 1000

        messages = self.build_messages(question, mode, contexts)
        t1 = time.perf_counter()
        gen = self.ollama.chat(
            model,
            messages,
            temperature=temperature,
            num_ctx=s.num_ctx,
            num_predict=s.num_predict,
            think=think,
        )
        t_generation = (time.perf_counter() - t1) * 1000

        result = {
            "question": question,
            "mode": mode,
            "model": model,
            "answer": gen["content"],
            "thinking": gen.get("thinking"),
            "contexts": contexts,
            "usage": gen["usage"],
            "timings_ms": {
                "retrieval": round(t_retrieval, 1),
                "generation": round(t_generation, 1),
                "total": round(t_retrieval + t_generation, 1),
                "ollama": gen["timings_ms"],
            },
            "params": {
                "top_k": top_k if mode == "rag" else 0,
                "retrieval": retrieval if mode == "rag" else None,
                "temperature": temperature,
                "think": think,
                "embed_model": s.embed_model,
                "collection": s.collection,
                "filters": filters or {},
            },
        }
        if include_prompt:
            result["prompt"] = {"system": messages[0]["content"], "user": messages[1]["content"]}
        return result

    # ----------------------------------------------------------------- health
    def health(self) -> dict:
        ollama_ok = self.ollama.is_alive()
        models = self.ollama.list_models() if ollama_ok else []
        try:
            collection = self.store.info()
            qdrant_ok = True
        except Exception as exc:  # noqa: BLE001
            collection, qdrant_ok = {"error": str(exc)}, False
        manifest_path = Path(self.settings.data_dir) / "manifest.json"
        return {
            "status": "ok" if ollama_ok and qdrant_ok and collection.get("points_count", 0) > 0 else "degraded",
            # El manifest se escribe al final de la ingesta (y se borra al empezar una nueva)
            "ingest_complete": manifest_path.exists(),
            "ollama": {"url": self.settings.ollama_url, "alive": ollama_ok, "models": models},
            "qdrant": {"url": self.settings.qdrant_url, "alive": qdrant_ok, "collection": collection},
            "defaults": {
                "llm_model": self.settings.llm_model,
                "embed_model": self.settings.embed_model,
                "top_k": self.settings.top_k,
                "retrieval": self.settings.retrieval_mode,
                "temperature": self.settings.temperature,
                "think": self.settings.llm_think,
            },
        }
