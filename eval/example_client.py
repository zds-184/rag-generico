"""Ejemplo mínimo de cómo un evaluador consumiría la API.

Lee preguntas de sample_questions.jsonl, las ejecuta en modo rag y llm, y guarda todo
(respuesta, contextos, prompt, tiempos, tokens) en eval/results/<timestamp>.jsonl.
Sobre ese archivo se pueden calcular métricas de retrieval (hit@k, MRR contra `expected_ids`)
y de generación (faithfulness, answer relevancy, correctness con LLM-as-judge, etc.).

Uso:  python eval/example_client.py [--api http://localhost:8000] [--modes rag,llm] [--top-k 5]
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import requests

HERE = Path(__file__).parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000")
    ap.add_argument("--questions", default=str(HERE / "sample_questions.jsonl"))
    ap.add_argument("--modes", default="rag,llm")
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--model", default=None)
    ap.add_argument("--retrieval", default=None, choices=["hybrid", "dense", "sparse"])
    args = ap.parse_args()

    questions = [json.loads(l) for l in Path(args.questions).read_text(encoding="utf-8").splitlines() if l.strip()]
    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{datetime.now():%Y%m%d_%H%M%S}.jsonl"

    hits = 0
    total_rag = 0
    with out_path.open("w", encoding="utf-8") as fh:
        for q in questions:
            for mode in args.modes.split(","):
                body = {"question": q["question"], "mode": mode, "top_k": args.top_k, "model": args.model,
                        "retrieval": args.retrieval}
                t0 = time.perf_counter()
                r = requests.post(f"{args.api}/query", json=body, timeout=900)
                r.raise_for_status()
                res = r.json()
                res["eval"] = {"id": q.get("id"), "expected_ids": q.get("expected_ids"), "reference": q.get("reference")}

                # métrica de retrieval trivial: ¿algún chunk recuperado pertenece a un objeto esperado?
                if mode == "rag" and q.get("expected_ids"):
                    total_rag += 1
                    got = {c["metadata"].get("attack_id") for c in res["contexts"]}
                    hit = bool(got & set(q["expected_ids"]))
                    hits += hit
                    res["eval"]["hit_at_k"] = hit

                fh.write(json.dumps(res, ensure_ascii=False) + "\n")
                print(f"[{mode:>3}] {time.perf_counter()-t0:6.1f}s  {q['question'][:70]}")

    if total_rag:
        print(f"\nhit@{args.top_k} (retrieval): {hits}/{total_rag} = {hits/total_rag:.2%}")
    print(f"resultados: {out_path}")


if __name__ == "__main__":
    main()
