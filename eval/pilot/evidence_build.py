"""Tabla de evidencia por hecho para el piloto (protocolo v2, §4).

Lee data/chunks.jsonl y questions.jsonl (solo lectura) y escribe evidence_pilot.json con, por pregunta, los hechos
H# de la referencia y todos los fragmentos del corpus que los sostienen:
  gold        fragmento listado en gold_point_ids de la pregunta
  alt         fragmento no gold que sostiene el hecho por sí solo
  alt-parcial fragmento que lo sostiene de forma indirecta o genérica (el evaluador decide)
Cada regla busca, en los fragmentos cuyo attack_id esté en `scope` ("*" = cualquiera), todos los patrones (regex).

Uso:  python eval/pilot/evidence_build.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHUNKS = ROOT / "data" / "chunks.jsonl"
QUESTIONS = Path(__file__).parent / "questions.jsonl"
OUT = Path(__file__).parent / "evidence_pilot.json"


def R(scope, *patterns, kind="auto"):
    return {"scope": scope, "patterns": list(patterns), "kind": kind}


# hecho = (id, texto, [reglas]). kind="auto" -> gold si el fragmento está en gold_point_ids, si no alt.
FACTS = {
    "p01": [
        ("H1", "M1038 Execution Prevention", [R(["T1059.001"], r"M1038")]),
        ("H2", "M1045 Code Signing", [R(["T1059.001"], r"M1045")]),
        ("H3", "M1026 Privileged Account Management", [R(["T1059.001"], r"M1026")]),
        ("H4", "M1049 Antivirus/Antimalware", [R(["T1059.001"], r"M1049")]),
        ("H5", "M1042 Disable or Remove Feature or Program (PowerShell/WinRM)",
         [R(["T1059.001"], r"M1042"), R(["T1059"], r"M1042", kind="alt-parcial")]),
    ],
    "p02": [
        ("H1", "Phishing pertenece a Initial Access", [R(["T1566"], r"initial-access|Initial Access")]),
        ("H2", "T1566.001 Spearphishing Attachment", [R(["T1566"], r"T1566\.001")]),
        ("H3", "T1566.002 Spearphishing Link", [R(["T1566"], r"T1566\.002")]),
        ("H4", "T1566.003 Spearphishing via Service", [R(["T1566"], r"T1566\.003")]),
        ("H5", "T1566.004 Spearphishing Voice", [R(["T1566"], r"T1566\.004")]),
    ],
    "p03": [
        ("H1", "Persistencia = el adversario intenta mantener su punto de apoyo", [R(["TA0003"], r"foothold")]),
        ("H2", "Conservar acceso pese a reinicios, cambios de credenciales u otras interrupciones", [R(["TA0003"], r"restart")]),
    ],
    "p04": [
        ("H1", "Cobalt Strike: herramienta comercial de acceso remoto / simulación de adversarios", [R(["S0154"], r"adversary simulation")]),
        ("H2", "Aprovecha capacidades de Metasploit y Mimikatz", [R(["S0154"], r"Metasploit")]),
    ],
    "p05": [
        ("H1", "APT29 usa Mimikatz (G0016 <-> S0002)",
         [R(["G0016"], r"S0002 Mimikatz"), R(["S0002"], r"G0016 APT29")]),
        ("H2", "Mimikatz implementa T1550.003 Pass the Ticket",
         [R(["S0002"], r"T1550\.003"), R(["T1550.003"], r"S0002 Mimikatz")]),
        ("H3", "Mimikatz implementa T1558.001 Golden Ticket",
         [R(["S0002"], r"T1558\.001"), R(["T1558.001"], r"S0002 Mimikatz")]),
        ("H4", "Mimikatz implementa T1558.002 Silver Ticket",
         [R(["S0002"], r"T1558\.002"), R(["T1558.002"], r"S0002 Mimikatz")]),
    ],
    "p06": [
        ("H1", "Lazarus usa T1059.001 PowerShell",
         [R(["G0032"], r"T1059\.001"), R("*", r"G0032", r"T1059\.001", kind="alt-parcial")]),
        ("H2", "Lazarus usa T1059.003 Windows Command Shell",
         [R(["G0032"], r"T1059\.003"), R("*", r"G0032", r"T1059\.003", kind="alt-parcial")]),
        ("H3", "Lazarus usa T1059.005 Visual Basic",
         [R(["G0032"], r"T1059\.005"), R("*", r"G0032", r"T1059\.005", kind="alt-parcial")]),
    ],
    "p07": [
        ("H1", "Nearest Neighbor Campaign: APT28 password spray contra servicios públicos",
         [R(["T1110.003", "G0007", "C0051"], r"Nearest Neighbor|C0051")]),
        ("H2", "Herramienta de fuerza bruta: ~4 intentos por hora por cuenta",
         [R(["T1110.003", "G0007"], r"four|4 .*per hour")]),
        ("H3", "Clúster de Kubernetes para password spray distribuido",
         [R(["T1110.003", "G0007"], r"Kubernetes")]),
    ],
    "p08": [
        ("H1", "M1027 Password Policies (NIST)", [R(["T1110.003"], r"M1027")]),
        ("H2", "M1032 Multi-factor Authentication", [R(["T1110.003"], r"M1032")]),
        ("H3", "M1036 Account Use Policies", [R(["T1110.003"], r"M1036")]),
    ],
    "p09": [
        ("H1", "M1031 Network Intrusion Prevention", [R(["T1566"], r"M1031")]),
        ("H2", "M1021 Restrict Web-Based Content", [R(["T1566"], r"M1021")]),
        ("H3", "M1017 User Training", [R(["T1566"], r"M1017")]),
        ("H4", "M1049 Antivirus/Antimalware", [R(["T1566"], r"M1049")]),
        ("H5", "M1054 Software Configuration (SPF, DKIM, DMARC)",
         [R(["T1566"], r"M1054"), R(["T1566"], r"SPF", r"DKIM")]),
        ("H6", "M1047 Audit", [R(["T1566"], r"M1047")]),
    ],
    # p10-p13: sin hechos (no respondibles); no hay evidencia que registrar.
}


def main():
    chunks = [json.loads(line) for line in CHUNKS.read_text(encoding="utf8").splitlines() if line.strip()]
    gold = {}
    for line in QUESTIONS.read_text(encoding="utf8").splitlines():
        q = json.loads(line)
        gold[q["id"]] = set(q["gold_point_ids"])

    out = {}
    problems = []
    for qid, facts in FACTS.items():
        out[qid] = []
        for fid, text, rules in facts:
            found = {}
            for rule in rules:
                for c in chunks:
                    if rule["scope"] != "*" and c["attack_id"] not in rule["scope"]:
                        continue
                    if not all(re.search(p, c["text"]) for p in rule["patterns"]):
                        continue
                    kind = rule["kind"]
                    if kind == "auto":
                        kind = "gold" if c["id"] in gold[qid] else "alt"
                    elif c["id"] in gold[qid]:
                        kind = "gold"
                    prev = found.get(c["id"])
                    order = {"gold": 0, "alt": 1, "alt-parcial": 2}
                    if prev is None or order[kind] < order[prev["kind"]]:
                        found[c["id"]] = {"point_id": c["id"], "attack_id": c["attack_id"],
                                          "chunk": f"{c['chunk_index']}/{c['n_chunks']}", "kind": kind}
            evidence = sorted(found.values(), key=lambda e: (e["kind"], e["attack_id"], e["chunk"]))
            if not evidence:
                problems.append(f"{qid} {fid}: sin evidencia en el corpus")
            out[qid].append({"fact": fid, "text": text, "evidence": evidence})
        # los gold declarados deben figurar como evidencia de algún hecho
        listed = {e["point_id"] for f in out[qid] for e in f["evidence"]}
        for g in gold[qid] - listed:
            problems.append(f"{qid}: gold {g} no aparece como evidencia de ningún hecho")

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf8")
    print(f"escrito {OUT}")
    for qid, facts in out.items():
        for f in facts:
            n = {k: sum(1 for e in f["evidence"] if e["kind"] == k) for k in ("gold", "alt", "alt-parcial")}
            print(qid, f["fact"], n)
    print("\nREVISAR:" if problems else "\nsin problemas")
    for p in problems:
        print(" -", p)


if __name__ == "__main__":
    main()
