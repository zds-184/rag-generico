"""Comprueba que la ingesta esté completa antes de una corrida (protocolo v2.2 §8, punto 2).

Compara tres conteos que deben coincidir: líneas de data/chunks.jsonl, n_chunks del manifest y puntos de la
colección en Qdrant (vía GET /health de la API). Sale con código 1 si difieren o falta el manifest.

Uso (desde RAG/):  python eval/pilot/check_ingest.py [--api http://localhost:8000]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import requests

HERE = Path(__file__).parent
DATA = HERE.parent.parent / "data"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def corpus_snapshot(data_dir: Path = DATA) -> dict:
    """Identidad exacta del corpus indexado: manifest de la ingesta + hash y nº de líneas de chunks.jsonl."""
    manifest_path, chunks_path = data_dir / "manifest.json", data_dir / "chunks.jsonl"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
    n_lines = sum(1 for l in chunks_path.open(encoding="utf-8") if l.strip()) if chunks_path.exists() else None
    return {
        "manifest": manifest,
        "chunks_jsonl_lines": n_lines,
        "chunks_jsonl_sha256": sha256_of(chunks_path) if chunks_path.exists() else None,
    }


def check(api: str, data_dir: Path = DATA) -> list[str]:
    """Devuelve la lista de problemas encontrados (vacía si la ingesta está completa)."""
    problems: list[str] = []
    snap = corpus_snapshot(data_dir)
    manifest, n_lines = snap["manifest"], snap["chunks_jsonl_lines"]
    if manifest is None:
        problems.append("falta data/manifest.json: la ingesta no terminó (o está en curso)")
    if n_lines is None:
        problems.append("falta data/chunks.jsonl")
    try:
        health = requests.get(f"{api}/health", timeout=30).json()
        points = health["qdrant"]["collection"].get("points_count")
        if not health.get("ingest_complete", False):
            problems.append("la API reporta ingest_complete = false")
    except Exception as exc:  # noqa: BLE001
        problems.append(f"no se pudo consultar {api}/health: {exc}")
        points = None
    if manifest and n_lines is not None and manifest.get("n_chunks") != n_lines:
        problems.append(f"manifest n_chunks={manifest.get('n_chunks')} != líneas de chunks.jsonl={n_lines}")
    if points is not None and n_lines is not None and points != n_lines:
        problems.append(f"puntos en Qdrant={points} != líneas de chunks.jsonl={n_lines}")
    if manifest and points is not None and manifest.get("points_count") != points:
        problems.append(f"manifest points_count={manifest.get('points_count')} != puntos en Qdrant={points}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000")
    args = ap.parse_args()
    problems = check(args.api)
    if problems:
        print("INGESTA INCOMPLETA O INCONSISTENTE:")
        for p in problems:
            print(f"  - {p}")
        return 1
    snap = corpus_snapshot()
    print(f"ingesta completa: {snap['chunks_jsonl_lines']} chunks = puntos en Qdrant; "
          f"ATT&CK {snap['manifest'].get('attack_versions')}; sha256(chunks.jsonl)={snap['chunks_jsonl_sha256'][:12]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
