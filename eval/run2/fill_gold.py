"""Rellena gold_point_ids de questions_propuesta.jsonl a partir de data/chunks.jsonl (corpus reingestado).

Para cada pregunta, `gold_evidence` = {attack_id: [fragmentos de texto que enuncian los hechos H#]}. Un chunk es gold si
pertenece a ese attack_id y contiene al menos uno de los fragmentos. Se ejecuta DESPUÉS de la reingesta (los point_id
cambian con ella) y antes de la corrida:

    python eval/run2/fill_gold.py            # escribe questions.jsonl junto a la propuesta y muestra el resumen
    python eval/run2/fill_gold.py --check    # solo comprueba, no escribe
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", default=str(HERE / "questions_propuesta.jsonl"))
    ap.add_argument("--chunks", default=str(ROOT / "data" / "chunks.jsonl"))
    ap.add_argument("--manifest", default=str(ROOT / "data" / "manifest.json"))
    ap.add_argument("--out", default=str(HERE / "questions.jsonl"))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    by_attack = defaultdict(list)
    with open(args.chunks, encoding="utf-8") as fh:
        for line in fh:
            c = json.loads(line)
            by_attack[c["attack_id"]].append(c)
    manifest = json.load(open(args.manifest, encoding="utf-8"))

    questions = [json.loads(l) for l in open(args.questions, encoding="utf-8") if l.strip()]
    problems = 0
    for q in questions:
        gold, detail = [], []
        for aid, needles in (q.get("gold_evidence") or {}).items():
            chunks = sorted(by_attack.get(aid, []), key=lambda c: c["chunk_index"])
            if not chunks:
                print(f"{q['id']}: {aid} no está en el corpus")
                problems += 1
                continue
            for needle in needles:
                hits = [c for c in chunks if needle in c["text"]]
                if not hits:
                    print(f"{q['id']}: {aid} no contiene {needle!r} en ningún chunk")
                    problems += 1
                for c in hits:
                    if c["id"] not in gold:
                        gold.append(c["id"])
                        detail.append(f"{aid}#{c['chunk_index'] + 1}/{c['n_chunks']}")
        q["gold_point_ids"] = gold
        q["gold_chunks_human"] = detail
        print(f"{q['id']} {q['answerability']:8} gold={len(gold):2}  {' '.join(detail)}")

    if problems:
        print(f"\n{problems} problema(s): revisar antes de correr", file=sys.stderr)
        return 1
    if args.check:
        return 0
    with open(args.out, "w", encoding="utf-8") as fh:
        for q in questions:
            q["corpus"] = {"attack_versions": manifest.get("attack_versions"), "n_chunks": manifest.get("n_chunks"),
                           "created_at": manifest.get("created_at")}
            fh.write(json.dumps(q, ensure_ascii=False) + "\n")
    print(f"\nescrito {args.out} ({len(questions)} preguntas); status sigue 'draft' hasta que se validen las referencias")
    return 0


if __name__ == "__main__":
    sys.exit(main())
