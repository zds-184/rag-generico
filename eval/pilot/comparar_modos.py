"""Deriva de la tabla por afirmación las notas y las cuatro lecturas de la comparación RAG vs LLM (protocolo v2, §3-§5).

Entrada (solo lectura): un CSV de afirmaciones (columnas de `afirmaciones_ejemplos.csv`), evidence_pilot.json (hechos por
pregunta) y questions.jsonl (para saber si hay parte no respondible). No escribe nada; imprime tablas.

Uso:  python eval/pilot/comparar_modos.py [afirmaciones.csv]
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent


def split(v):
    return [x for x in (v or "").split(";") if x]


def derive(rows, hechos, has_unans):
    """rows: afirmaciones de una respuesta; hechos: ids H# de la pregunta."""
    facts = [r for r in rows if r["tipo"] == "hecho"]
    covered = {h for r in rows if r["vs_ref"] == "CORRECTA" and r["zona"] == "ref" for h in split(r["hecho_ref"])}
    covered_cited = {h for r in rows if r["vs_ref"] == "CORRECTA" and r["respaldo"] == "SOSTENIDA"
                     for h in split(r["hecho_ref"])}
    H = len(hechos)
    inc = [r for r in facts if r["vs_ref"] == "INCORRECTA"]
    abs_e = [r for r in rows if r["tipo"] == "abstencion" and r["vs_ref"] == "INCORRECTA"]
    no_abs = [r for r in facts if r["vs_ref"] == "FUERA_REF" and r["zona"] == "no_resp"]
    fuera = [r for r in facts if r["vs_ref"] == "FUERA_REF"]
    # N2 (§3.4)
    C = len(covered)
    if H == 0:
        n2 = 0 if no_abs else 2
    elif C == H and not (inc or abs_e or no_abs):
        n2 = 2
    elif C == 0:
        n2 = 0
    else:
        n2 = 1
    # N3 (§3.4), solo modo con respaldo
    sup = [r for r in facts if r["respaldo"] == "SOSTENIDA"]
    n3 = "N/A" if not facts or not any(r["respaldo"] for r in facts) else (2 if len(sup) == len(facts) else (0 if not sup else 1))
    # B: estado en la parte respondible y en la no respondible
    if H:
        if C == H and not abs_e:
            e_resp = "responde"
        elif C > 0:
            e_resp = "responde parcial" + (" + ABS-E" if abs_e else "")
        elif abs_e:
            e_resp = "se abstiene (ABS-E)"
        else:
            e_resp = "no cubre"
    else:
        e_resp = "N/A"
    if has_unans:
        if no_abs:
            e_nores = "responde (NO-ABS)"
        elif any(r["zona"] == "no_resp" and r["vs_ref"] == "CORRECTA" for r in rows):
            e_nores = "se abstiene"
        else:
            e_nores = "no la aborda"
    else:
        e_nores = "N/A"
    alertas = []
    if inc or abs_e or no_abs:
        alertas.append("CRITICA(" + ",".join(n for n, v in (("INC", inc), ("ABS-E", abs_e), ("NO-ABS", no_abs)) if v) + ")")
    if any(r["respaldo"] in ("SIN-RESPALDO", "CITA-X") for r in facts):
        alertas.append("RESPALDO")
    return {
        "alertas": " ".join(alertas) or "-",
        "H": H, "C": C, "cobertura": f"{C}/{H}" if H else "-",
        "INC": f"{len(inc)}/{len(facts)}" if facts else "-",
        "n_fuera_ref": len(fuera), "N2": n2, "N3": n3,
        "estado_respondible": e_resp, "estado_no_respondible": e_nores,
        "prec_citas": f"{len(sup)}/{len(facts)}" if facts and any(r["respaldo"] for r in facts) else "-",
        "cob_citas": f"{len(covered_cited)}/{H}" if H else "-",
        "SR": sum(r["respaldo"] == "SIN-RESPALDO" for r in facts),
        "CITA-X": sum(r["respaldo"] == "CITA-X" for r in facts),
        "SIN-C": sum(r["respaldo"] == "SIN-CITA" for r in facts),
    }


def main(path):
    ev = json.loads((HERE / "evidence_pilot.json").read_text(encoding="utf8"))
    unans = {}
    for line in (HERE / "questions.jsonl").read_text(encoding="utf8").splitlines():
        q = json.loads(line)
        unans[q["id"]] = bool(q["unanswerable_part"])
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    groups = {}
    for r in rows:
        groups.setdefault((r["qid"], r["modo"]), []).append(r)
    res = {}
    for (qid, modo), rs in sorted(groups.items()):
        res[(qid, modo)] = derive(rs, [h["fact"] for h in ev.get(qid, [])], unans[qid])

    print("A. Fidelidad a la referencia (cobertura de hechos · afirmaciones INCORRECTA/afirmaciones de hecho)")
    print("D. Fuera de referencia (n afirmaciones FUERA_REF)   |   N2/N3 derivados")
    print(f"{'id':4} {'modo':4} {'cobert.':8} {'INC':6} {'FUERA':6} {'N2':3} {'N3':4} alertas")
    for (qid, modo), d in res.items():
        print(f"{qid:4} {modo:4} {d['cobertura']:8} {d['INC']:6} {d['n_fuera_ref']:<6} {d['N2']:<3} {d['N3']!s:4} {d['alertas']}")
    print("\nB. Abstención (estado en la parte respondible / en la parte no respondible)")
    for (qid, modo), d in res.items():
        print(f"{qid:4} {modo:4} respondible: {d['estado_respondible']:22} no respondible: {d['estado_no_respondible']}")
    print("\nC. Respaldo documental (solo RAG): precisión de citas · cobertura de citas · SIN-RESPALDO / CITA-X / SIN-CITA")
    for (qid, modo), d in res.items():
        if modo == "rag":
            print(f"{qid:4} {modo:4} {d['prec_citas']:6} {d['cob_citas']:6} {d['SR']}/{d['CITA-X']}/{d['SIN-C']}")
    print("\nTotales descriptivos (hechos cubiertos ÷ hechos de las preguntas incluidas)")
    for modo in ("rag", "llm"):
        c = sum(d["C"] for (q, m), d in res.items() if m == modo)
        h = sum(d["H"] for (q, m), d in res.items() if m == modo)
        print(f"{modo}: {c}/{h}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else HERE / "afirmaciones_ejemplos.csv")
