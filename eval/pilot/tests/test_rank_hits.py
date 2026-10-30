"""Prueba del desempate determinista en la recuperación (protocol_v2.2 §6.2).

Ejecutar desde RAG/:  python eval/pilot/tests/test_rank_hits.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "app"))

from rag.vectorstore import rank_hits  # noqa: E402


def _hits():
    # Empate en la frontera como en p01 del piloto: dos puntos con score RRF 0.25
    return [
        {"id": "aaaa", "score": 0.5, "payload": {}},
        {"id": "cccc", "score": 0.3333333333, "payload": {}},
        {"id": "952ba9e9-02f1-5a73-9728-d18d3b697266", "score": 0.25, "payload": {}},
        {"id": "3176af7f-1b20-500d-8754-9e2746f08472", "score": 0.25, "payload": {}},
        {"id": "zzzz", "score": 0.2, "payload": {}},
    ]


def test_tie_broken_by_id_regardless_of_input_order():
    expected = None
    for seed in range(20):
        hits = _hits()
        random.Random(seed).shuffle(hits)
        got = [h["id"] for h in rank_hits(hits, 3)]
        expected = expected or got
        assert got == expected, (seed, got)
    assert expected == ["aaaa", "cccc", "3176af7f-1b20-500d-8754-9e2746f08472"]


def test_score_order_preserved_and_truncated():
    out = rank_hits(_hits(), 2)
    assert [h["score"] for h in out] == [0.5, 0.3333333333]


if __name__ == "__main__":
    fails = 0
    for fn in (test_tie_broken_by_id_regardless_of_input_order, test_score_order_preserved_and_truncated):
        try:
            fn(); print(f"OK   {fn.__name__}")
        except AssertionError as exc:
            fails += 1; print(f"FAIL {fn.__name__}: {exc}")
    sys.exit(1 if fails else 0)
