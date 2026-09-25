# Piloto de evaluación diagnóstica del RAG — protocolo v1.1

Sistema bajo prueba: RAG genérico de `RAG/` (qwen3:4b-instruct + granite-embedding:30m + Qdrant, corpus MITRE ATT&CK Enterprise v19.2).

> v1.1 (2026-09-25): tras calificar la corrida `20260922_064359` se añaden reglas de aplicación de la rúbrica (§3.1),
> limitaciones del sistema detectadas (§4), resultados del piloto (§6) y casos ambiguos (§7). La rúbrica de §3 no cambia,
> para que la calificación ya hecha siga siendo válida.

## 1. Pregunta de investigación (borrador v1)

> ¿Permite un protocolo de evaluación manual de cuatro niveles (corpus, recuperación, generación y citas)
> localizar de forma consistente el origen de los errores de un sistema RAG local sobre MITRE ATT&CK?

Sub-preguntas:

| | Sub-pregunta | Nivel | Cómo se responde en el piloto |
|---|---|---|---|
| RQ1 | ¿Existía en el corpus la información necesaria (total, parcial, nula)? | N0 corpus | Diseño de las preguntas con ground truth verificado en `chunks.jsonl` |
| RQ2 | ¿La recuperación trajo los fragmentos que la contienen y en qué posición? | N1 recuperación | Automático: `gold_point_ids` ∩ top-k (hit@k, rango y recall@k) |
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
  Se guarda en `results/<run>/config.json`. Límites de tokens del `.env`: ventana `LLM_NUM_CTX=4096` (prompt + respuesta)
  y respuesta máxima `LLM_NUM_PREDICT=1024`. Con `temperature=0` la decodificación es *greedy* (siempre el token más
  probable), por lo que los filtros de muestreo por defecto del modelo en Ollama (`top_k=20`, `top_p=0.8`) no intervienen.
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

### 3.1 Reglas de aplicación (añadidas en v1.1)

**Fuente de verdad.** La `reference` de cada pregunta, redactada desde el corpus, es la vara de medir de **ambos** modos.
El modo LLM no lee el corpus, pero se califica contra la misma referencia; "tiene respuesta" es una decisión del
diseño (N0), no una afirmación sobre lo que el modelo sabe.

**N1**
- *hit@k* es binario por pregunta: cuenta 1 si llega al menos un gold, aunque falten otros. Se reporta además
  **recall@k** = gold recuperados ÷ gold totales (`gold_points_found` / `gold_points_total` en la traza).
- N1 es una aproximación: la respuesta puede estar también en un fragmento no gold (*evidencia alternativa*, frecuente
  en ATT&CK porque la misma relación aparece en el documento del grupo, del software y de la técnica). No se corrige N1;
  se anota en el comentario y la pregunta queda como candidata a ampliar sus `gold_point_ids` en v2.

**N3**
- **N/A** sólo cuando la respuesta no hace ninguna afirmación basada en los fragmentos (abstención total) y en todas
  las filas del modo LLM. No se deja vacío: vacío = sin calificar.
- Abstención **parcial** (pregunta parcial): se califica N3 sobre la parte que sí se respondió.
- Afirmación correcta pero **sin fragmento que la sostenga** ("correcto sin soporte", p. ej. respondida de memoria):
  N2 puede ser alto, N3 baja.
- El promedio N3 de la hoja `Resumen` excluye los N/A (promedia sólo respuestas con afirmaciones).

**Diagnóstico: coherencia con N2/N3**
- **OK** sólo si N2 = 2 y N3 ∈ {2, N/A}. Abstención correcta en pregunta nula = OK (no E3).
- **E3** exige N2 = 2 y N3 numérico < 2; con N3 = N/A no puede haber E3.
- **Gold parcial** (N1 = SI pero `gold_points_found` < `gold_points_total`): E1 si lo que falta en la respuesta estaba en
  el gold que no llegó; E2 si estaba en lo que sí llegó. Justificar en el comentario.
- Abstención errónea (la información llegó y el modelo dijo "no está"): N2 = 0, N3 = N/A, diagnóstico E2.

**Modo LLM**
- E1 y E3 son imposibles (no hay búsqueda ni fragmentos que citar).
- **E0** = pregunta sin respuesta según la referencia (nula, o la parte no respondible de una parcial) y el modelo no se
  abstuvo. El nombre "corpus" es impreciso en este modo; candidato a renombrar en v2 (p. ej. `E0-no-abstencion`).
- **E2** = la pregunta tiene referencia y N2 < 2; en este modo suele significar que el modelo no lo sabía o lo recordó mal,
  no que razonara mal sobre una evidencia. Por eso RAG vs LLM se compara con **N2**, no con el conteo de E2.
- Respuesta cierta en el mundo real pero **fuera de la referencia** (p. ej. p10/p11 existen en ATT&CK Mobile/ICS): se
  califica contra la referencia (N2 = 0, E0) y se anota "correcto fuera de la referencia" para reportarlo aparte.

## 4. Limitaciones conocidas del corpus (nivel N0)

1. **Sólo el dominio Enterprise** (v19.2). Mobile e ICS no están ingestados → preguntas sobre T14xx (Mobile) o T08xx (ICS) son no respondibles por construcción (p10, p11).
2. **Sólo contenido oficial de ATT&CK**: descripciones, relaciones grupo↔técnica↔software↔mitigación↔detección y ejemplos de procedimiento. No hay estadísticas de incidencia, precios, recomendaciones de productos, normas externas (PCI, ISO), historial de versiones de herramientas ni noticias.
3. **Idioma**: todo el corpus está en inglés; las preguntas en español se responden con evidencia en inglés.
4. **Ejemplos de procedimiento truncados a 25 por técnica** (`MAX_PROCEDURE_EXAMPLES=25` en la ingesta). Para técnicas muy usadas, la lista "quién la usa" está incompleta a propósito.
5. **Chunking por caracteres (1.200, solape 150)**: listas largas quedan repartidas en varios fragmentos; el RAG sólo recibe 5.
6. **Defecto de chunking detectado (2026-09-21)**: en documentos largos algunos fragmentos repiten el texto de solape dos veces. Ejemplos verificados: `G0032` chunk 4/6 (la lista de técnicas se reinicia tras "T108"), `G0016` chunk 3/4, `M1038` chunks 4–5/5, `S0154` chunk 3/4, `T1110.003` chunk 4/9. Efecto: ruido y texto truncado a mitad de línea dentro del contexto; no impide la recuperación. **Decisión**: el corpus se congela tal cual para el piloto (cambiarlo a mitad invalidaría las comparaciones) y el defecto se registra como limitación; la corrección en `app/rag/chunking.py` + reingesta (~60 min CPU) queda para después del piloto.
7. **Foto temporal**: ATT&CK v19.2 descargado el 2026-09-12; nada posterior existe en el corpus.
8. **Dos tipos de pregunta no respondible**: (a) sin respuesta en ninguna fuente (p08 %, p09 producto recomendado,
   p12 "más usada en 2026", p13 T1059.099 inexistente) y (b) fuera del corpus pero existentes en el mundo real (p10 Mobile,
   p11 ICS, precio de p04 y posiblemente p06). En (b) el modo LLM puede acertar desde su entrenamiento; ver §3.1.

### Limitaciones del sistema detectadas durante el piloto

- **Truncado de la respuesta (N2).** `LLM_NUM_PREDICT=1024` cortó a mitad la respuesta de p01 en modo LLM
  (`completion_tokens = 1024`). Detectable en la hoja `Prompts`; se califica tal cual y se anota.
- **Ventana de contexto.** Con `top_k=5` el prompt RAG ocupó 1.201–1.854 tokens (máx. 1.931 con la respuesta, 47 % de
  4.096). Si se sube `top_k` (≈350 tokens por fragmento) hay que subir `LLM_NUM_CTX`: Ollama descarta el inicio del prompt
  sin error cuando no cabe, y se perderían las instrucciones del sistema.
- **Embeddings.** `granite-embedding:30m` trunca a 512 tokens (un fragmento de 1.200 caracteres ≈ 300–400, cabe) y está
  orientado al inglés: con preguntas en español la similitud se deja llevar en parte por el idioma (en una prueba, un texto
  en español sin relación puntuó más que uno en inglés sobre otro tema de ATT&CK). Relevante para el efecto del idioma.

### Limitación del sistema detectada durante el piloto (nivel N1): empates

**Recuperación híbrida no determinista en empates (2026-09-22).** Al repetir la pregunta p01 en Streamlit, el usuario obtuvo
en rango 5 `T1059.010` mientras la traza del piloto registraba `S0393`. Verificado con 5 llamadas a `POST /retrieve`:
ambos fragmentos tienen **el mismo score RRF (0.2500)** y Qdrant rompe el empate de forma arbitraria (3 veces `S0393`,
2 veces `T1059.010`). Consecuencias para el protocolo:

- La traza (`traces.jsonl`) es el **único registro válido** de lo que el LLM recibió en esa corrida; una re-ejecución en la UI
  no reproduce necesariamente el mismo contexto. Las columnas automáticas del Excel nunca se corrigen a mano.
- Si un fragmento gold queda en la frontera del top-k empatado con otro, el veredicto N1 (y por tanto el diagnóstico E1/E2)
  puede cambiar entre ejecuciones. `run_pilot.py --check-ties <corrida>` detecta estos casos (`ties.json`) para marcarlos
  como inestables al calificar.
- Es un hallazgo del sistema bajo prueba, no del protocolo: se reporta como limitación de reproducibilidad del RAG
  (punto de mejora: desempate determinista en `vectorstore.search`, p. ej. por `point_id`). No se corrige durante el piloto.
- Resultado en la corrida `20260922_064359` (`ties.json`): empate en la frontera en p01, p04 y p12, **ningún gold en la
  frontera** → los veredictos N1 de esa corrida son estables.

## 5. Ejecución

```bash
cd D:/DS_USFQ/CAPSTON/RAG
python eval/pilot/run_pilot.py
```

Genera `eval/pilot/results/<timestamp>/` con `config.json`, `traces.jsonl`, `calificacion.xlsx` y `summary.json`.
Si se interrumpe: `python eval/pilot/run_pilot.py --resume eval/pilot/results/<timestamp>`.
Regenerar el Excel sin volver a consultar (**sobrescribe la calificación manual**):
`python eval/pilot/run_pilot.py --rebuild-xlsx eval/pilot/results/<timestamp>`.
Detectar empates en la frontera del top-k: `python eval/pilot/run_pilot.py --check-ties eval/pilot/results/<timestamp>`.
Duración medida en CPU (4 núcleos), corrida `20260922_064359`: RAG ≈ 94 s y LLM ≈ 65 s por respuesta → 26 respuestas
≈ 35 min. En modo RAG el grueso es la lectura del prompt (~50–90 s), no la generación.

## 6. Resultados de la corrida `20260922_064359`

13 preguntas × 2 modos, una calificación manual (un evaluador). Cifras de la hoja `Resumen` tras aplicar las reglas de
§3.1 (dos correcciones pendientes en el Excel al 2026-09-25: p10–p13 RAG E3 → OK; p01 LLM OK → E2).

| Métrica | RAG | LLM |
|---|---|---|
| N2 promedio (0–2) | 1,23 (62 %) | 0,54 (27 %) |
| N3 promedio (0–2, 7 respuestas con afirmaciones) | 1,71 (86 %) | N/A |
| N1 hit@5 · recall@5 (9 respondibles) | 6/9 (67 %) · 56 % | N/A |
| OK / E0 / E1 / E2 / E3 | 7 / 0 / 5 / 1 / 0 | 2 / 3 / 0 / 8 / 0 |

N2 por subconjunto:

| Subconjunto | RAG | LLM |
|---|---|---|
| Nulas (p10–p13) | 2,00 | 0,50 |
| Respondibles (p01–p09) | 0,89 | 0,56 |
| ↳ gold llegó (p02, p03, p04, p06, p07, p09) | 1,17 | 0,67 |
| ↳ gold no llegó (p01, p05, p08) | 0,33 | 0,33 |

Lectura:
1. El RAG duplica el N2 del mismo LLM; la mayor ventaja es la **abstención**: 4/4 en nulas frente a 3/4 inventadas.
2. En respondibles la ventaja depende de la recuperación: si el gold no llega, RAG = LLM (0,33). **E1 es el error
   dominante del RAG** (5 de 6).
3. El RAG es **conservador**: se abstuvo en p01, p06, p08 y p09; en p06 lo hizo aunque el gold llegó (único E2).
4. Cuando afirma, cita bien (N3 = 1,71, sin E3). El caso débil es p05: "APT29 usa Mimikatz" sin fragmento que lo sostenga.
5. El protocolo distingue causas que una nota única no separa (p01 y p06 tienen N2 = 0: E1 y E2 respectivamente).

Advertencias: muestra pequeña (13 preguntas), un solo evaluador, una sola corrida; RQ6 (re-calificación a ciegas) pendiente.

## 7. Casos ambiguos encontrados en la rúbrica

| Caso | Pregunta(s) | Resolución en v1.1 (§3.1) | Propuesta v2 |
|---|---|---|---|
| Gold parcial: N1 = SI pero falta un gold | p02, p09 | E1 o E2 según dónde estaba lo omitido, justificado en comentario | Reportar recall@k y usarlo en la regla |
| Evidencia alternativa en fragmentos no gold | p05 | Calificar normal, anotar | Ampliar `gold_point_ids` |
| Correcto sin soporte en el contexto | p05 ("Sí") | N3 baja | Nivel explícito de *groundedness* por afirmación |
| LLM correcto fuera de la referencia | p10, p11 (y precio de p04) | Calificar contra la referencia, anotar | Valor propio de diagnóstico o sólo nulas del tipo (a) |
| Nombre "E0-corpus" en modo LLM | p10, p11, p13 | Se interpreta como "no se abstuvo" | Renombrar `E0-no-abstencion` |
| N3 ante abstención | p08, p10–p13 | N/A, nunca 0 | — (se calificó distinto en filas equivalentes: insumo para RQ6) |
| Respuesta truncada por límite de tokens | p01 LLM | Calificar tal cual, anotar | Subir `LLM_NUM_PREDICT` o marcar truncados |

## 8. Entregables acordados

1. RQ v1 + sub-preguntas (sección 1).
2. Matriz comparativa RAGAS / RAGChecker / ARES / FActScore / RefChecker (+ ALCE para citas) — **hecha**:
   `D:/DS_USFQ/CAPSTON/matriz_comparativa_evaluacion_RAG.xlsx`. Brecha principal: ninguno de los cinco evalúa si las citas
   sostienen lo afirmado (N3).
3. Piloto: `questions.jsonl`, `traces.jsonl`, `calificacion.xlsx` calificada (2 correcciones pendientes, §6), tabla de
   diagnósticos (§6) y casos ambiguos (§7). Pendiente: re-calificación a ciegas para RQ6.
