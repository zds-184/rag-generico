"""Calcula `llegó` por hecho y N1 (NINGUNA/PARTE/TODA) para una corrida (protocolo v2, §4).

Cruza traces.jsonl (solo lectura) con evidence_pilot.json. Escribe <corrida>/n1_v2.json y un resumen en pantalla.
No modifica traces.jsonl ni calificacion.xlsx.

Uso:  python eval/pilot/evidence_check.py eval/pilot/results/20260922_064359
"""
import json
import sys
from pathlib import Path

EVIDENCE = Path(__file__).parent / "evidence_pilot.json"
QUESTIONS = Path(__file__).parent / "questions.jsonl"


def best(ctx_rank, evidence, kinds):
    ranks = [ctx_rank[e["point_id"]] for e in evidence if e["kind"] in kinds and e["point_id"] in ctx_rank]
    return min(ranks) if ranks else None


def main(run):
    run = Path(run)
    ev = json.loads(EVIDENCE.read_text(encoding="utf8"))
    questions = {}
    for line in QUESTIONS.read_text(encoding="utf8").splitlines():
        q = json.loads(line)
        questions[q["id"]] = q
    result = {}
    for line in (run / "traces.jsonl").read_text(encoding="utf8").splitlines():
        t = json.loads(line)
        if t["mode"] != "rag":
            continue
        qid = t["eval"]["id"]
        ctx_rank = {c["point_id"]: c["rank"] for c in t["contexts"]}
        facts = []
        for f in ev.get(qid, []):
            r_gold = best(ctx_rank, f["evidence"], {"gold"})
            r_alt = best(ctx_rank, f["evidence"], {"alt"})
            r_par = best(ctx_rank, f["evidence"], {"alt-parcial"})
            if r_gold:
                llego, rank = "SI", r_gold
            elif r_alt:
                llego, rank = "ALT", r_alt
            elif r_par:
                llego, rank = "ALT-P", r_par
            else:
                llego, rank = "NO", None
            facts.append({"fact": f["fact"], "text": f["text"], "llego": llego, "rank": rank})
        total = len(facts)
        arrived = sum(1 for f in facts if f["llego"] in ("SI", "ALT"))
        arrived_p = sum(1 for f in facts if f["llego"] in ("SI", "ALT", "ALT-P"))
        if total == 0:
            n1 = "N/A"
        elif arrived == 0:
            n1 = "NINGUNA"
        elif arrived == total:
            n1 = "TODA"
        else:
            n1 = "PARTE"
        ranks = [f["rank"] for f in facts if f["rank"]]
        gold_ids = set(questions[qid]["gold_point_ids"])
        found = len(gold_ids & set(ctx_rank))
        result[qid] = {
            "n1": n1, "hechos_llegaron": f"{arrived}/{total}",
            "hechos_llegaron_incl_alt_parcial": f"{arrived_p}/{total}",
            "mejor_rango": min(ranks) if ranks else None,
            "hit_gold": found > 0 if gold_ids else None,
            "recall_gold": f"{found}/{len(gold_ids)}" if gold_ids else None,
            "hechos": facts,
        }
    (run / "n1_v2.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf8")
    print(f"{'id':4} {'N1':8} {'hechos':7} {'+ALT-P':7} {'rango':6} {'gold hit':9} recall_gold   llegó por hecho")
    for qid in sorted(result):
        r = result[qid]
        per = " ".join(f"{f['fact']}={f['llego']}" for f in r["hechos"])
        print(f"{qid:4} {r['n1']:8} {r['hechos_llegaron']:7} {r['hechos_llegaron_incl_alt_parcial']:7} "
              f"{str(r['mejor_rango']):6} {str(r['hit_gold']):9} {str(r['recall_gold']):12} {per}")


if __name__ == "__main__":
    main(sys.argv[1])
