"""Capa de acceso a Qdrant: vector denso ("dense") + vector disperso BM25 ("bm25").

Modos de búsqueda:
  dense  -> similitud coseno sobre embeddings
  sparse -> BM25 (TF calculado en cliente, IDF aplicado por Qdrant)
  hybrid -> ambas búsquedas en paralelo y fusión Reciprocal Rank Fusion (RRF)
"""
from __future__ import annotations

import time
from typing import Literal

from qdrant_client import QdrantClient, models

DENSE = "dense"
SPARSE = "bm25"
RetrievalMode = Literal["dense", "sparse", "hybrid"]


class VectorStore:
    def __init__(self, url: str, collection: str, api_key: str | None = None):
        self.client = QdrantClient(url=url, api_key=api_key or None, timeout=120)
        self.collection = collection

    # ---------------------------------------------------------------- estado
    def wait_ready(self, retries: int = 60, delay: float = 3.0) -> None:
        for _ in range(retries):
            try:
                self.client.get_collections()
                return
            except Exception:
                time.sleep(delay)
        raise RuntimeError("Qdrant no responde")

    def exists(self) -> bool:
        return self.client.collection_exists(self.collection)

    def count(self) -> int:
        return self.client.count(self.collection, exact=True).count if self.exists() else 0

    def info(self) -> dict:
        if not self.exists():
            return {"name": self.collection, "exists": False, "points_count": 0}
        info = self.client.get_collection(self.collection)
        vectors = info.config.params.vectors
        dense = vectors.get(DENSE) if isinstance(vectors, dict) else vectors
        sparse = info.config.params.sparse_vectors or {}
        return {
            "name": self.collection,
            "exists": True,
            "status": str(info.status),
            "points_count": self.count(),
            "vector_size": getattr(dense, "size", None),
            "distance": str(getattr(dense, "distance", None)),
            "sparse_vectors": sorted(sparse.keys()),
            "hybrid_capable": SPARSE in sparse,
        }

    # ----------------------------------------------------------- escritura
    def recreate(self, dim: int) -> None:
        if self.exists():
            self.client.delete_collection(self.collection)
        self.client.create_collection(
            self.collection,
            vectors_config={DENSE: models.VectorParams(size=dim, distance=models.Distance.COSINE)},
            sparse_vectors_config={SPARSE: models.SparseVectorParams(modifier=models.Modifier.IDF)},
        )
        for key in ("object_type", "domain", "attack_id", "tactics", "platforms"):
            self.client.create_payload_index(
                self.collection, field_name=key, field_schema=models.PayloadSchemaType.KEYWORD
            )

    def upsert(
        self,
        ids: list[str],
        dense_vectors: list[list[float]],
        sparse_vectors: list[tuple[list[int], list[float]]],
        payloads: list[dict],
    ) -> None:
        points = [
            models.PointStruct(
                id=pid,
                vector={DENSE: dv, SPARSE: models.SparseVector(indices=sv[0], values=sv[1])},
                payload=pl,
            )
            for pid, dv, sv, pl in zip(ids, dense_vectors, sparse_vectors, payloads)
        ]
        self.client.upsert(self.collection, points=points, wait=True)

    # ------------------------------------------------------------- lectura
    @staticmethod
    def _build_filter(filters: dict[str, list[str]] | None) -> models.Filter | None:
        if not filters:
            return None
        must = [
            models.FieldCondition(key=key, match=models.MatchAny(any=list(values)))
            for key, values in filters.items()
            if values
        ]
        return models.Filter(must=must) if must else None

    def search(
        self,
        dense_vector: list[float] | None,
        sparse_vector: tuple[list[int], list[float]] | None,
        top_k: int,
        mode: RetrievalMode = "hybrid",
        filters: dict[str, list[str]] | None = None,
        candidates_factor: int = 4,
    ) -> list[dict]:
        qfilter = self._build_filter(filters)
        sparse = models.SparseVector(indices=sparse_vector[0], values=sparse_vector[1]) if sparse_vector else None

        if mode == "dense":
            res = self.client.query_points(
                self.collection, query=dense_vector, using=DENSE, limit=top_k, query_filter=qfilter, with_payload=True
            )
        elif mode == "sparse":
            res = self.client.query_points(
                self.collection, query=sparse, using=SPARSE, limit=top_k, query_filter=qfilter, with_payload=True
            )
        else:  # hybrid: RRF sobre los candidatos de ambas búsquedas
            n = top_k * candidates_factor
            res = self.client.query_points(
                self.collection,
                prefetch=[
                    models.Prefetch(query=dense_vector, using=DENSE, limit=n, filter=qfilter),
                    models.Prefetch(query=sparse, using=SPARSE, limit=n, filter=qfilter),
                ],
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                limit=top_k,
                with_payload=True,
            )
        return [{"id": str(p.id), "score": float(p.score), "payload": p.payload or {}} for p in res.points]
