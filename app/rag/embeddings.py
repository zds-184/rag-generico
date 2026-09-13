"""Embeddings vía Ollama con batching y prefijos de tarea opcionales."""
from __future__ import annotations

from .ollama_client import OllamaClient

# Modelos que recomiendan prefijos de tarea distintos para documento / consulta
AUTO_PREFIXES = {
    "nomic-embed": ("search_document: ", "search_query: "),
}


class Embedder:
    def __init__(
        self,
        client: OllamaClient,
        model: str,
        batch_size: int = 32,
        doc_prefix: str | None = None,
        query_prefix: str | None = None,
    ):
        self.client = client
        self.model = model
        self.batch_size = max(1, batch_size)
        auto = next((p for k, p in AUTO_PREFIXES.items() if model.lower().startswith(k)), ("", ""))
        self.doc_prefix = auto[0] if doc_prefix is None else doc_prefix
        self.query_prefix = auto[1] if query_prefix is None else query_prefix
        self._dim: int | None = None

    def dimension(self) -> int:
        if self._dim is None:
            self._dim = len(self.embed_query("dimension probe"))
        return self._dim

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = [self.doc_prefix + t for t in texts[i : i + self.batch_size]]
            out.extend(self.client.embed(self.model, batch))
        return out

    def embed_query(self, text: str) -> list[float]:
        return self.client.embed(self.model, [self.query_prefix + text])[0]
