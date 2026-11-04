"""Vuelca afirmaciones_extraidas.json en la hoja Afirmaciones de un libro v2.3 RECIÉN generado (sin calificar).

Solo escribe qid, modo, afirmación y cita_n; tipo, vs_ref, hecho_ref, zona, respaldo y nota quedan vacíos para el evaluador.
Se niega a tocar un libro que ya tenga filas en Afirmaciones o 'llegó' rellenado (protege calificaciones).

    python eval/run2/fill_afirmaciones.py eval/run2/calificacion_v2_run2.xlsx
"""
import json
import sys
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent


def main(book: str) -> int:
    wb = openpyxl.load_workbook(book)
    ws = wb["Afirmaciones"]
    if any(r[0] or r[3] for r in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True)):
        print("Afirmaciones ya tiene filas: no se toca", file=sys.stderr)
        return 1
    if any(r[4] for r in wb["Hechos"].iter_rows(min_row=2, values_only=True)):
        print("Hechos ya tiene 'llegó' rellenado: no se toca", file=sys.stderr)
        return 1
    data = json.loads((HERE / "afirmaciones_extraidas.json").read_text(encoding="utf-8"))
    hdr = [c.value for c in ws[1]]
    ci = {name: i + 1 for i, name in enumerate(hdr)}
    # orden: el de la hoja Respuestas (misma ordenación de preguntas que el libro)
    order = []
    for r in wb["Respuestas"].iter_rows(min_row=2, values_only=True):
        if r[0]:
            order.append((r[0], r[1]))
    rows = sorted(data["afirmaciones"], key=lambda a: order.index((a[0], a[1])))
    for i, (qid, modo, texto, cita) in enumerate(rows, 2):
        ws.cell(i, ci["qid"], qid)
        ws.cell(i, ci["modo"], modo)
        ws.cell(i, ci["afirmación"], texto)
        if cita:
            ws.cell(i, ci["cita_n"], cita)
    wk = wb["Config"]
    n = wk.max_row + 1
    wk.cell(n + 1, 1, "extracción de afirmaciones")
    wk.cell(n + 1, 2, data["_nota"])
    wsG = wb["Guia"]
    g = wsG.max_row + 1
    wsG.cell(g, 1, "Afirmaciones prellenadas")
    wsG.cell(g, 2, "La columna 'afirmación' viene prellenada desde eval/run2/afirmaciones_extraidas.json (extracción asistida, sin "
                   "juicio). Revisa cada fila contra la respuesta: parte, une o reescribe lo que haga falta y añade filas al final si "
                   "faltan. Luego califica tipo, vs_ref, hecho_ref, zona y respaldo como en el piloto.")
    wb.save(book)
    print(f"{len(rows)} afirmaciones escritas en {book}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
