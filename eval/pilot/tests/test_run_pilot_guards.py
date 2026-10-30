"""Pruebas de las guardas de la corrida reproducible (protocol_v2.2 §8, puntos 3-6), sin API ni Qdrant.

Ejecutar desde RAG/:  python eval/pilot/tests/test_run_pilot_guards.py
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import check_ingest  # noqa: E402
import run_pilot  # noqa: E402

HEALTH = {"defaults": {"llm_model": "qwen3:4b-instruct", "embed_model": "granite-embedding:30m", "top_k": 5,
                       "retrieval": "hybrid", "temperature": 0.1, "think": False, "num_ctx": 4096, "num_predict": 1024},
          "qdrant": {"collection": {"points_count": 7244}}, "ingest_complete": True}
CORPUS = {"manifest": {"attack_versions": {"enterprise-attack": "19.2"}, "created_at": "2026-11-01T00:00:00",
                       "n_chunks": 7244, "chunk_size": 1200, "chunk_overlap": 150, "points_count": 7244},
          "chunks_jsonl_lines": 7244, "chunks_jsonl_sha256": "abc"}


def _args(**kw) -> argparse.Namespace:
    base = dict(api="http://x", model=None, retrieval="hybrid", top_k=5, temperature=0.0, modes="rag,llm", force=False)
    base.update(kw)
    return argparse.Namespace(**base)


def test_config_records_generation_limits_and_corpus():
    cfg = run_pilot.build_config(_args(), HEALTH, CORPUS)
    assert cfg["num_ctx"] == 4096 and cfg["num_predict"] == 1024
    assert cfg["corpus"]["chunks_jsonl_sha256"] == "abc" and cfg["corpus"]["attack_versions"] == {"enterprise-attack": "19.2"}


def test_resume_mismatch_detected():
    saved = run_pilot.build_config(_args(), HEALTH, CORPUS)
    same = run_pilot.build_config(_args(), HEALTH, CORPUS)
    assert run_pilot.config_mismatch(saved, same) == []
    assert run_pilot.config_mismatch(saved, run_pilot.build_config(_args(top_k=8), HEALTH, CORPUS)) == ["top_k"]
    other_corpus = {**CORPUS, "chunks_jsonl_sha256": "zzz"}
    assert run_pilot.config_mismatch(saved, run_pilot.build_config(_args(), HEALTH, other_corpus)) == ["corpus"]
    other_limits = {**HEALTH, "defaults": {**HEALTH["defaults"], "num_predict": 2048}}
    assert run_pilot.config_mismatch(saved, run_pilot.build_config(_args(), other_limits, CORPUS)) == ["num_predict"]
    # Una corrida del piloto (config.json antiguo, sin num_ctx/corpus) no puede reanudarse con la versión nueva
    old = json.loads((HERE.parent / "results" / "20260922_064359" / "config.json").read_text(encoding="utf-8"))
    assert set(run_pilot.config_mismatch(old, same)) >= {"num_ctx", "num_predict", "corpus"}


def test_workbook_not_overwritten_without_force():
    questions = [{"id": "q1", "lang": "es", "answerability": "none", "question": "?", "reference": "-"}]
    done = {("q1", "rag"): {"mode": "rag", "answer": "x", "contexts": [], "eval": {"id": "q1", "retrieval": {}}}}
    cfg = run_pilot.build_config(_args(), HEALTH, CORPUS)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "calificacion.xlsx"
        assert run_pilot.write_workbook_protected(questions, done, cfg, out, force=False) is True
        out.write_bytes(b"calificaciones manuales")
        assert run_pilot.write_workbook_protected(questions, done, cfg, out, force=False) is False
        assert out.read_bytes() == b"calificaciones manuales"
        assert run_pilot.write_workbook_protected(questions, done, cfg, out, force=True) is True
        assert out.read_bytes() != b"calificaciones manuales"


def test_gold_snapshot_written():
    questions = run_pilot.load_questions(HERE.parent / "questions.jsonl")
    with tempfile.TemporaryDirectory() as tmp:
        missing = run_pilot.snapshot_gold(questions, Path(tmp))
        snap = [json.loads(l) for l in (Path(tmp) / "questions_snapshot.jsonl").read_text(encoding="utf-8").splitlines()]
        gold = [json.loads(l) for l in (Path(tmp) / "gold_chunks.jsonl").read_text(encoding="utf-8").splitlines()]
        assert len(snap) == len(questions)
        assert len(gold) == sum(len(q.get("gold_point_ids") or []) for q in questions)
        assert missing == 0 and all(g["text"] for g in gold), "todos los gold deben tener texto en chunks.jsonl"


def test_check_ingest_detects_mismatch():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "chunks.jsonl").write_text('{"id":"a"}\n{"id":"b"}\n', encoding="utf-8")
        (d / "manifest.json").write_text(json.dumps({"n_chunks": 3, "points_count": 3}), encoding="utf-8")
        problems = check_ingest.check("http://127.0.0.1:9", d)  # API inalcanzable a propósito
        assert any("n_chunks=3" in p for p in problems)
        assert any("health" in p for p in problems)


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"OK   {name}")
            except Exception as exc:  # noqa: BLE001
                fails += 1; print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    sys.exit(1 if fails else 0)
