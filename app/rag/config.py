"""Configuración centralizada leída desde variables de entorno (.env)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env(name: str, default=None):
    value = os.getenv(name)
    return default if value is None or value.strip() == "" else value.strip()


def _bool(name: str, default: bool = False) -> bool:
    return str(_env(name, default)).lower() in ("1", "true", "yes", "on")


def _list(name: str, default: str) -> list[str]:
    return [x.strip() for x in str(_env(name, default)).split(",") if x.strip()]


@dataclass
class Settings:
    # Conexiones
    qdrant_url: str = _env("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key: str | None = _env("QDRANT_API_KEY")
    collection: str = _env("QDRANT_COLLECTION", "mitre_attack")
    ollama_url: str = _env("OLLAMA_URL", "http://localhost:11434")
    request_timeout: float = float(_env("REQUEST_TIMEOUT", 600))

    # Modelos
    llm_model: str = _env("LLM_MODEL", "qwen3:4b")
    embed_model: str = _env("EMBED_MODEL", "nomic-embed-text")
    embed_batch_size: int = int(_env("EMBED_BATCH_SIZE", 32))
    embed_doc_prefix: str | None = _env("EMBED_DOC_PREFIX")
    embed_query_prefix: str | None = _env("EMBED_QUERY_PREFIX")

    # Generación
    llm_think: bool = _bool("LLM_THINK", False)
    temperature: float = float(_env("LLM_TEMPERATURE", 0.1))
    num_ctx: int = int(_env("LLM_NUM_CTX", 8192))
    num_predict: int = int(_env("LLM_NUM_PREDICT", 1024))

    # Retrieval / chunking
    top_k: int = int(_env("TOP_K", 5))
    retrieval_mode: str = _env("RETRIEVAL_MODE", "hybrid")  # hybrid | dense | sparse
    chunk_size: int = int(_env("CHUNK_SIZE", 1200))
    chunk_overlap: int = int(_env("CHUNK_OVERLAP", 150))

    # Corpus
    attack_domains: list[str] = field(default_factory=lambda: _list("ATTACK_DOMAINS", "enterprise-attack"))
    attack_base_url: str = _env(
        "ATTACK_BASE_URL", "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master"
    )
    max_procedure_examples: int = int(_env("MAX_PROCEDURE_EXAMPLES", 25))
    refresh_corpus: bool = _bool("REFRESH_CORPUS", False)
    force_reingest: bool = _bool("FORCE_REINGEST", False)
    data_dir: str = _env("DATA_DIR", "/data")


settings = Settings()
