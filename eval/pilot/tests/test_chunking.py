"""Pruebas del chunking (defecto de solape duplicado, protocol_v2.2 §6.1 punto 6).

Ejecutar desde RAG/:  python eval/pilot/tests/test_chunking.py   (o pytest, si está instalado)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "app"))

from rag.chunking import split_text  # noqa: E402

CHUNK_SIZE, OVERLAP = 1200, 150
DOCS = ROOT / "data" / "documents.jsonl"
# Documentos en los que se verificó el defecto (fragmentos que repiten el solape dos veces)
KNOWN_BAD = ("G0032", "G0016", "M1038", "S0154", "T1110.003")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _load_docs(attack_ids: tuple[str, ...]) -> dict[str, str]:
    out = {}
    with DOCS.open(encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            aid = d["metadata"].get("attack_id")
            if aid in attack_ids:
                out[aid] = d["text"]
    return out


def _synthetic_long_text() -> str:
    # Un "párrafo" sin puntuación de >4 chunks, como las listas "## Techniques used" de los grupos
    return "# Doc\n\n" + " - ".join(f"T{1000 + i:04d} Technique number {i}" for i in range(220))


def duplicated_overlap(chunks: list[str], overlap: int = OVERLAP) -> list[int]:
    """Índices de chunks cuyo inicio contiene dos veces el final del chunk anterior."""
    bad = []
    for i in range(1, len(chunks)):
        probe = chunks[i - 1][-40:]
        if chunks[i][: 2 * overlap + 60].count(probe) > 1:
            bad.append(i)
    return bad


def test_no_duplicated_overlap():
    texts = {"synthetic": _synthetic_long_text()}
    if DOCS.exists():
        texts.update(_load_docs(KNOWN_BAD))
    for name, text in texts.items():
        chunks = split_text(text, CHUNK_SIZE, OVERLAP)
        assert len(chunks) > 1, name
        assert duplicated_overlap(chunks) == [], f"{name}: solape duplicado en chunks {duplicated_overlap(chunks)}"


def test_chunk_size_bound():
    texts = {"synthetic": _synthetic_long_text()}
    if DOCS.exists():
        texts.update(_load_docs(KNOWN_BAD))
    for name, text in texts.items():
        for i, c in enumerate(split_text(text, CHUNK_SIZE, OVERLAP)):
            assert len(c) <= CHUNK_SIZE, f"{name}: chunk {i} tiene {len(c)} > {CHUNK_SIZE}"


def test_overlap_present_and_text_preserved():
    text = _synthetic_long_text()
    chunks = split_text(text, CHUNK_SIZE, OVERLAP)
    joined = _norm(" ".join(chunks))
    normalized = _norm(text)
    # Nada del texto se pierde: cada ventana de 40 caracteres aparece en los chunks
    for start in range(0, len(normalized) - 40, 97):
        assert normalized[start : start + 40] in joined, f"texto perdido en {start}"
    # Hay solape (el final de un chunk reaparece al inicio del siguiente), de ~OVERLAP caracteres
    for i in range(1, len(chunks)):
        assert chunks[i - 1][-30:] in chunks[i][: OVERLAP + 40], f"sin solape entre {i - 1} y {i}"


if __name__ == "__main__":
    fails = 0
    for fn in (test_no_duplicated_overlap, test_chunk_size_bound, test_overlap_present_and_text_preserved):
        try:
            fn()
            print(f"OK   {fn.__name__}")
        except AssertionError as exc:
            fails += 1
            print(f"FAIL {fn.__name__}: {exc}")
    sys.exit(1 if fails else 0)
