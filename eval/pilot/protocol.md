# Piloto de evaluación diagnóstica del RAG — protocolo v1

Sistema bajo prueba: RAG genérico de `RAG/` (qwen3:4b-instruct + granite-embedding:30m + Qdrant, corpus MITRE ATT&CK Enterprise v19.2).

## 1. Pregunta de investigación (borrador v1)

> ¿Permite un protocolo de evaluación manual de cuatro niveles (corpus, recuperación, generación y citas)
> localizar de forma consistente el origen de los errores de un sistema RAG local sobre MITRE ATT&CK?

Sub-preguntas:

| | Sub-pregunta | Nivel | Cómo se responde en el piloto |
|---|---|---|---|
| RQ1 | ¿Existía en el corpus la información necesaria (total, parcial, nula)? | N0 corpus | Diseño de las preguntas con ground truth verificado en `chunks.jsonl` |
| RQ2 | ¿La recuperación trajo los fragmentos que la contienen y en qué posición? | N1 recuperación | Automático: `gold_point_ids` ∩ top-k |
| RQ3 | Dado el contexto, ¿el LLM construyó una respuesta correcta y fiel (sin inventar ni omitir)? | N2 generación | Calificación manual 0/1/2 contra la referencia |
| RQ4 | ¿Cada afirmación está ligada a una cita `[n]` cuyo fragmento la sostiene? | N3 citas | Calificación manual 0/1/2 con la hoja `Contextos` |
| RQ5 | ¿Cuánto cambia N2 al usar el mismo LLM con y sin recuperación? | comparativo | Misma pregunta en modo `rag` y `llm`, misma configuración |
| RQ6 | ¿El protocolo es consistente (mismo veredicto al re-calificar)? | validación | Re-calificar 6–8 respuestas a ciegas una semana después |

Resultado secundario (no en la RQ): aporte de la recuperación (RQ5) y efecto del idioma de la pregunta (9 es / 4 en).

## 2. Diseño del piloto

- 13 preguntas en `questions.jsonl`: 5 completas, 4 parciales, 4 no respondibles; 9 en español, 4 en inglés.
- Cada pregunta lleva `gold_point_ids` (fragmentos exactos de `data/chunks.jsonl` que contienen la respuesta), una
  `reference` redactada **sólo** a partir de esos fragmentos y, si aplica, la `unanswerable_part` verificada como ausente.
- Configuración fija para todas: recuperación `hybrid`, `top_k=5`, `temperature=0`, `think=false`, modelo por defecto.
  Se guarda en `results/<run>/config.json`.
- Cada respuesta se guarda íntegra (`traces.jsonl`): respuesta, contextos con `point_id` y `score`, prompt exacto, tokens y tiempos.

## 3. Rúbrica de calificación

Una fila por pregunta × modo en `calificacion.xlsx` (hoja `Calificacion`). Columnas verdes = automáticas; amarillas = manuales.

| Nivel | Valores | Regla |
|---|---|---|
| N0 corpus (auto) | completa / parcial / nula | Viene del diseño de la pregunta |
| N1 recuperación (auto, sólo RAG) | SI / NO + rango | Algún fragmento gold entre los top-k |
| N2 respuesta (manual) | 2 / 1 / 0 | 2 correcta y completa · 1 a medias · 0 incorrecta o inventada. Nula: 2 = se abstuvo, 0 = inventó. Parcial: 2 = responde lo disponible y se abstiene del resto · 1 = responde lo disponible pero inventa el resto · 0 = erra lo disponible |
| N3 citas (manual, sólo RAG) | 2 / 1 / 0 / N/A | 2 toda afirmación citada y sostenida · 1 alguna sin cita o cita que no la sostiene · 0 sin citas o equivocadas · N/A si se abstuvo |
| Diagnóstico (manual) | OK / E0-corpus / E1-recuperacion / E2-generacion / E3-citas | **Primer eslabón que falló**: E0 no estaba y no se abstuvo → E1 estaba pero no llegó → E2 llegó y aun así N2<2 → E3 N2=2 pero N3<2 |

Modo LLM: sólo N2 y diagnóstico (OK / E0-corpus / E2-generacion).

## 4. Limitaciones conocidas del corpus (nivel N0)

1. **Sólo el dominio Enterprise** (v19.2). Mobile e ICS no están ingestados → preguntas sobre T14xx (Mobile) o T08xx (ICS) son no respondibles por construcción (p10, p11).
2. **Sólo contenido oficial de ATT&CK**: descripciones, relaciones grupo↔técnica↔software↔mitigación↔detección y ejemplos de procedimiento. No hay estadísticas de incidencia, precios, recomendaciones de productos, normas externas (PCI, ISO), historial de versiones de herramientas ni noticias.
3. **Idioma**: todo el corpus está en inglés; las preguntas en español se responden con evidencia en inglés.
4. **Ejemplos de procedimiento truncados a 25 por técnica** (`MAX_PROCEDURE_EXAMPLES=25` en la ingesta). Para técnicas muy usadas, la lista "quién la usa" está incompleta a propósito.
5. **Chunking por caracteres (1.200, solape 150)**: listas largas quedan repartidas en varios fragmentos; el RAG sólo recibe 5.
6. **Defecto de chunking detectado (2026-09-21)**: en documentos largos algunos fragmentos repiten el texto de solape dos veces. Ejemplos verificados: `G0032` chunk 4/6 (la lista de técnicas se reinicia tras "T108"), `G0016` chunk 3/4, `M1038` chunks 4–5/5, `S0154` chunk 3/4, `T1110.003` chunk 4/9. Efecto: ruido y texto truncado a mitad de línea dentro del contexto; no impide la recuperación. **Decisión**: el corpus se congela tal cual para el piloto (cambiarlo a mitad invalidaría las comparaciones) y el defecto se registra como limitación; la corrección en `app/rag/chunking.py` + reingesta (~60 min CPU) queda para después del piloto.
7. **Foto temporal**: ATT&CK v19.2 descargado el 2026-09-12; nada posterior existe en el corpus.

## 5. Ejecución

```bash
cd D:/DS_USFQ/CAPSTON/RAG
python eval/pilot/run_pilot.py
```

Genera `eval/pilot/results/<timestamp>/` con `config.json`, `traces.jsonl`, `calificacion.xlsx` y `summary.json`.
Si se interrumpe: `python eval/pilot/run_pilot.py --resume eval/pilot/results/<timestamp>`.
Duración estimada en CPU (4 núcleos): 26 respuestas × 2–4 min ≈ 1–1,5 h.

## 6. Entregables al director

1. RQ v1 + sub-preguntas (sección 1).
2. Matriz comparativa RAGAS / RAGChecker / ARES / FActScore / RefChecker (+ ALCE para citas) — pendiente.
3. Piloto: `questions.jsonl`, `traces.jsonl`, `calificacion.xlsx` calificada, tabla de diagnósticos y casos ambiguos encontrados en la rúbrica.
