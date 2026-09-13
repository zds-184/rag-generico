"""Ingesta: descarga MITRE ATT&CK -> documentos -> chunks -> embeddings -> Qdrant.

Ejecutar:  python -m rag.ingest
Idempotente: si la colección ya tiene puntos y FORCE_REINGEST != true, no hace nada.
Exporta además /data/documents.jsonl, /data/chunks.jsonl y /data/manifest.json
para construir datasets de evaluación sobre exactamente el mismo corpus indexado.
"""
from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .chunking import split_text
from .config import settings
from .corpus_mitre import build_documents, download_domain, load_bundle
from .embeddings import Embedder
from .ollama_client import OllamaClient
from .sparse import document_sparse_vector
from .vectorstore import VectorStore


def log(msg: str) -> None:
    print(f"[ingest] {msg}", flush=True)


def main() -> None:
    data_dir = Path(settings.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    log(f"Qdrant={settings.qdrant_url} collection={settings.collection}")
    store = VectorStore(settings.qdrant_url, settings.collection, settings.qdrant_api_key)
    store.wait_ready()

    if store.exists() and store.count() > 0 and not settings.force_reingest:
        log(f"la colección ya tiene {store.count()} puntos; se omite la ingesta (FORCE_REINGEST=true para rehacer)")
        return

    # Un manifest sólo existe cuando la ingesta terminó; se borra al empezar una nueva
    (data_dir / "manifest.json").unlink(missing_ok=True)

    log(f"Ollama={settings.ollama_url} embed_model={settings.embed_model}")
    ollama = OllamaClient(settings.ollama_url, timeout=settings.request_timeout)
    ollama.wait_alive()
    for _ in range(60):
        if ollama.has_model(settings.embed_model):
            break
        log(f"esperando que el modelo {settings.embed_model} esté disponible...")
        time.sleep(5)
    else:
        raise RuntimeError(f"El modelo de embeddings {settings.embed_model} no está en Ollama")

    embedder = Embedder(
        ollama, settings.embed_model, settings.embed_batch_size, settings.embed_doc_prefix, settings.embed_query_prefix
    )

    # ---- 1. corpus -> documentos
    documents = []
    versions: dict[str, str | None] = {}
    for domain in settings.attack_domains:
        path = download_domain(domain, settings.attack_base_url, settings.data_dir, settings.refresh_corpus)
        objects = load_bundle(path)
        docs, version = build_documents(objects, domain, settings.max_procedure_examples)
        versions[domain] = version
        log(f"{domain}: ATT&CK v{version} -> {len(objects)} objetos STIX -> {len(docs)} documentos")
        documents.extend(docs)

    # ---- 2. documentos -> chunks
    records: list[dict] = []
    for doc in documents:
        chunks = split_text(doc.text, settings.chunk_size, settings.chunk_overlap)
        for i, chunk in enumerate(chunks):
            # Los chunks posteriores al primero heredan el título para no perder contexto
            text = chunk if i == 0 else f"# {doc.title}\n{chunk}"
            records.append(
                {
                    "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc.id}#{i}")),
                    "text": text,
                    "payload": {**doc.metadata, "chunk_index": i, "n_chunks": len(chunks), "text": text},
                }
            )
    log(f"{len(documents)} documentos -> {len(records)} chunks (size={settings.chunk_size}, overlap={settings.chunk_overlap})")

    with (data_dir / "documents.jsonl").open("w", encoding="utf-8") as fh:
        for d in documents:
            fh.write(json.dumps({"id": d.id, "title": d.title, "text": d.text, "metadata": d.metadata}, ensure_ascii=False) + "\n")
    with (data_dir / "chunks.jsonl").open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps({"id": r["id"], **r["payload"]}, ensure_ascii=False) + "\n")

    # ---- 3. embeddings -> Qdrant
    dim = embedder.dimension()
    log(f"dimensión de embeddings = {dim}; (re)creando colección")
    store.recreate(dim)

    batch = settings.embed_batch_size
    t0 = time.perf_counter()
    for i in range(0, len(records), batch):
        part = records[i : i + batch]
        texts = [r["text"] for r in part]
        dense = embedder.embed_documents(texts)
        sparse = [document_sparse_vector(t) for t in texts]
        store.upsert([r["id"] for r in part], dense, sparse, [r["payload"] for r in part])
        done = i + len(part)
        if done % (batch * 10) == 0 or done == len(records):
            elapsed = time.perf_counter() - t0
            rate = done / elapsed if elapsed else 0
            eta = (len(records) - done) / rate if rate else 0
            log(f"{done}/{len(records)} chunks indexados ({rate:.1f} chunks/s, ETA {eta/60:.1f} min)")

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "collection": settings.collection,
        "embed_model": settings.embed_model,
        "embed_dim": dim,
        "sparse_vector": "bm25 (k1=1.2, b=0.75, IDF en Qdrant)",
        "doc_prefix": embedder.doc_prefix,
        "query_prefix": embedder.query_prefix,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
        "domains": settings.attack_domains,
        "attack_versions": versions,
        "n_documents": len(documents),
        "n_chunks": len(records),
        "points_count": store.count(),
        "elapsed_s": round(time.perf_counter() - t0, 1),
    }
    (data_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"listo: {manifest['points_count']} puntos en '{settings.collection}' en {manifest['elapsed_s']} s")


if __name__ == "__main__":
    main()
