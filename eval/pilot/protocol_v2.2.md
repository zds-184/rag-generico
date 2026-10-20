# Evaluación diagnóstica de un RAG local sobre MITRE ATT&CK — protocolo v2.2 (consolidado)

**Qué es este documento.** Reúne en un solo texto el protocolo v1.1 (`protocol.md`) y el borrador v2 (`protocol_v2.md`),
más lo decidido después (alertas, plantilla de Excel, matriz con ALCE y CiteEval). No reemplaza a los originales: `protocol.md`,
`protocol_v2.md`, `questions.jsonl` y la corrida `20260922_064359` siguen intactos y son la referencia del piloto.

**Estado (2026-10-19).** Borrador para la reunión con el director. Lo marcado **[pendiente]** no está decidido o no se ha hecho.

| Versión | Fecha | Qué incorpora |
|---|---|---|
| v1 | 2026-09 | Rúbrica N0–N3 de una nota por nivel; piloto de 13 preguntas × 2 modos |
| v1.1 | 2026-09-25 | Reglas de aplicación, limitaciones del sistema, resultados y casos ambiguos del piloto |
| v2 (borrador) | 2026-10-12 | Calificación por afirmación; N1 por evidencia; comparación con y sin RAG; alertas; plantilla Excel |
| **v2.2** | 2026-10-19 | Consolidación de v1.1 y v2 en un documento; matriz con ALCE/CiteEval; plan de validación y de corrida reproducible |

Alcance acordado con el director: **evaluar y diagnosticar** las respuestas. El proyecto no es una optimización del RAG.

---

## 1. Pregunta de investigación y sub-preguntas

> ¿Permite un protocolo de evaluación manual por afirmación, en cuatro niveles (corpus, recuperación, generación y citas),
> localizar de forma consistente el origen de los errores de un sistema RAG local sobre MITRE ATT&CK?

| | Sub-pregunta | Nivel | Cómo se responde |
|---|---|---|---|
| RQ1 | ¿Existía en el corpus la información necesaria (total, parcial, nula)? | N0 corpus | Diseño de las preguntas con referencia verificada en `chunks.jsonl` |
| RQ2 | ¿La recuperación trajo la evidencia necesaria: ninguna, parte o toda? | N1 recuperación | Automático por hecho, aceptando evidencia alternativa (§4.1) |
| RQ3 | Dado el contexto, ¿cada afirmación es correcta, completa y fiel a la referencia? | N2 generación | Calificación manual por afirmación; N2 derivado (§3) |
| RQ4 | ¿Cada afirmación está ligada a una cita cuyo fragmento la sostiene? | N3 citas | Calificación manual por afirmación; N3 derivado (§3, §4.2) |
| RQ5 | ¿En qué se diferencian el mismo modelo con y sin recuperación, frente a una referencia común? | comparativo | Cuatro lecturas separadas (§5) |
| RQ6 | ¿El protocolo es consistente? | validación | Re-calificación a ciegas por el mismo evaluador y juez exploratorio **[pendiente de aprobación del director]** (§7) |

Cambios respecto de v1.1: RQ2 pasa de "hit@k de fragmentos gold" a evidencia por hecho; RQ3 y RQ4 pasan de una nota global
a afirmaciones; RQ5 deja de ser "cuánto cambia N2"; RQ6 ya no se reduce a re-calificar 6–8 respuestas (el director pidió
evaluación independiente, §7). Resultado secundario (no en la RQ): efecto del idioma de la pregunta (9 es / 4 en en el piloto).

## 2. Diseño del piloto (v1.1, sin cambios)

Sistema bajo prueba: RAG genérico de `RAG/` (qwen3:4b-instruct + granite-embedding:30m + Qdrant, corpus MITRE ATT&CK
Enterprise v19.2).

- 13 preguntas en `questions.jsonl`: 5 completas, 4 parciales, 4 no respondibles; 9 en español, 4 en inglés.
- Cada pregunta lleva `gold_point_ids` (fragmentos exactos de `data/chunks.jsonl` con la respuesta), una `reference`
  redactada **solo** a partir de esos fragmentos y, si aplica, la `unanswerable_part` verificada como ausente.
- Configuración fija: recuperación `hybrid`, `top_k=5`, `temperature=0`, `think=false`, modelo por defecto (guardada en
  `results/<run>/config.json`). Límites del `.env`: ventana `LLM_NUM_CTX=4096` (prompt + respuesta) y respuesta máxima
  `LLM_NUM_PREDICT=1024`. Con `temperature=0` la decodificación es *greedy*, por lo que los filtros de muestreo de Ollama
  (`top_k=20`, `top_p=0.8`) no intervienen.
- Cada respuesta se guarda íntegra (`traces.jsonl`): respuesta, contextos con `point_id` y `score`, prompt exacto, tokens y tiempos.

## 3. Qué se califica

Una respuesta se descompone en **afirmaciones atómicas** (máx. ≈6; si hay más, las que sustentan la referencia). Cada
afirmación se juzga en **dos ejes independientes**:

- **Corrección** frente a la `reference`, que es la misma para ambos modos. La cobertura del corpus (N0) es la condición de
  referencia: que algo no esté en el corpus no lo hace falso.
- **Respaldo** frente a los fragmentos que el sistema recibió (solo modo RAG).

Una respuesta puede tener varios problemas a la vez; no se elige solo el primero. Se distinguen tres situaciones que la nota
única de v1.1 mezclaba: **incorrecta** (contradice la referencia), **incompleta** (omite hechos de la referencia) y **correcta
pero sin respaldo** en los fragmentos recibidos.

### 3.1 Hoja `Hechos` (una vez por pregunta)

La referencia se descompone en hechos atómicos `H1..Hn` (n = 0 en preguntas nulas). Para la parte no respondible se registra
`unanswerable_part`. En modo RAG se añade por corrida la columna `llegó` (SI / ALT / ALT-P / NO), calculada como en §4.1.
Es la base de las omisiones y de E1 frente a E2.

### 3.2 Hoja `Afirmaciones` (una fila por afirmación × modo)

| Columna | Valores |
|---|---|
| `tipo` | `hecho` (afirma algo) · `abstencion` (dice que no hay información / no puede responder) |
| `vs_ref` | `CORRECTA` · `INCORRECTA` · `FUERA_REF` (ni confirma ni contradice la referencia) |
| `hecho_ref` | `H#` que cubre una afirmación `CORRECTA`; varios separados por `;` |
| `zona` | `ref` (por defecto) o `no_resp` (responde a la parte no respondible) |
| `respaldo` (solo RAG, solo `hecho`) | `SOSTENIDA` (con cita [n] cuyo fragmento la sostiene) · `CITA-X` (cita, pero ese fragmento no la sostiene) · `SIN-CITA` (sin cita, pero algún fragmento recibido la sostiene) · `SIN-RESPALDO` (ningún fragmento recibido la sostiene, tenga cita o no) |
| `cita_n`, `fragmento_sostiene` | rango [n] citado; rango del fragmento que realmente la sostiene (o vacío) |
| `nota` | texto libre |

Aclaraciones surgidas al calificar los ejemplos (`ejemplos_calificados_v2.md`):

- **Abstención vs. afirmación de ausencia.** `abstencion` = el modelo dice que *el contexto o él no tiene* la información
  ("los pasajes no dicen…"). Una afirmación sobre la fuente ("ATT&CK no documenta…", "no hay mitigaciones") es un `hecho`
  y puede ser `INCORRECTA`.
- **Listas cerradas.** Los elementos extra que la referencia no incluye son `FUERA_REF` (se reportan aparte como extras), no
  `INCORRECTA`; solo se marca `INCORRECTA` lo que contradice la referencia. En modo RAG un extra además recibe `respaldo`.
- **`llegó`** se determina leyendo los fragmentos recibidos (no solo `gold_points_found`), para registrar evidencia alternativa.

Fuera de la tabla: filas `OMISION` por cada `H#` de la referencia que ninguna afirmación `CORRECTA` cubre, e indicador
`TRUNC` por respuesta si `completion_tokens` alcanza el límite (`LLM_NUM_PREDICT`).

### 3.3 Códigos de problema (derivados de las columnas, no se escriben a mano)

| Código | Se genera cuando |
|---|---|
| `INC` | `tipo=hecho` y `vs_ref=INCORRECTA` |
| `OMI` | existe fila `OMISION` (hecho de la referencia sin cubrir) |
| `ABS-E` | `tipo=abstencion` y `vs_ref=INCORRECTA` (niega algo que la referencia sí contiene) |
| `NO-ABS` | `tipo=hecho`, `vs_ref=FUERA_REF` y responde a la `unanswerable_part` o a una pregunta nula (afirma sin base en referencia ni corpus) |
| `SIN-R` | `respaldo=SIN-RESPALDO` (correcta o no) |
| `CITA-X` | `respaldo=CITA-X` |
| `SIN-C` | `respaldo=SIN-CITA` |
| `TRUNC` | respuesta truncada |

Se aplican aunque la respuesta sea incorrecta. Una abstención correcta (`tipo=abstencion`, `vs_ref=CORRECTA`, sobre la parte
no respondible) no genera código. Un `FUERA_REF` que no responde a la parte no respondible (dato extra, cierto o no) se
reporta aparte como "fuera de la referencia"; no cuenta como error.

### 3.4 Notas derivadas

Sea H = nº de hechos de la referencia y C = nº de hechos cubiertos por afirmaciones `CORRECTA`.

**N2 (correcta y completa).**
- H = 0 (pregunta nula): **2** si no hay `NO-ABS`, **0** si lo hay.
- H > 0: **2** si C = H y no hay `INC`, `ABS-E` ni `NO-ABS`; **0** si C = 0; **1** en los demás casos.

**N3 (citas, solo RAG)**, sobre las afirmaciones `hecho`: **N/A** si no hay ninguna (abstención total); **2** si todas son
`SOSTENIDA`; **0** si ninguna lo es; **1** en los demás casos. En modo LLM, N3 es siempre N/A.

**Sin topes (decisión 2026-10-12).** N2 y N3 son descriptivos y monótonos: no hay reglas del tipo "si hay X entonces N2 = 0".
Los problemas graves no se esconden en la nota; se señalan con las alertas (§3.6). Por eso p06 (RAG) y p09 (LLM) dan N2 = 1
aunque el piloto les puso 0: el piloto mezclaba cobertura y veredicto final en un solo número.

### 3.5 Diagnóstico: lista de causas

| Etiqueta | Se asigna cuando |
|---|---|
| `E0-no-abstencion` | hay `NO-ABS` (renombrada desde "E0-corpus"; mismo significado en ambos modos) |
| `E1-recuperacion` | hay `OMI`, `INC` o `ABS-E` sobre un hecho con `llegó = NO` |
| `E2-generacion` | hay `OMI`, `INC` o `ABS-E` sobre un hecho con `llegó = SI/ALT` |
| `E3-citas` | hay `CITA-X`, `SIN-C` o `SIN-R` |
| `OK` | ninguna de las anteriores |

- Una respuesta lleva todas las etiquetas que apliquen (p. ej. `E2 + E3`). La columna "primer eslabón" se deriva con el orden
  E0 → E1 → E2 → E3 para poder comparar con el piloto.
- **Modo LLM**: no hay recuperación ni fragmentos; `llegó` y `respaldo` no aplican, así que solo pueden aparecer
  `E0-no-abstencion` y `E2-generacion` (aquí significa "no lo sabía o lo recordó mal", no que razonara mal sobre evidencia).
  `SIN-R` no se genera.
- `TRUNC` se reporta como indicador aparte, no como causa E.

### 3.6 Alertas derivadas (política, separada de la medición)

La **medición** (afirmaciones → códigos, cobertura, N2, N3) es fija y lleva la versión de la rúbrica. La **política** decide
qué merece atención y es configurable sin tocar la medición. Política por defecto:

| Alerta | Se activa cuando la respuesta tiene |
|---|---|
| `CRITICA` | `ABS-E`, `NO-ABS` o `INC` |
| `RESPALDO` | `SIN-R` o `CITA-X` (y `SIN-C`, como aviso menor) |
| `TRUNC` | respuesta truncada |

Las alertas no cambian N2 ni N3; se reportan en la columna `alertas`. Esta separación está pensada para el módulo de
evaluación y auditoría continua: la medición es una función pura y versionada, y cada despliegue puede cambiar la política.

## 4. Recuperación (N1) y citas

### 4.1 N1 por evidencia, no por fragmento gold

El piloto medía N1 como "llegó algún `gold_point_id`". Eso ignora (a) que haya llegado solo una parte de lo necesario y
(b) que el mismo hecho esté en fragmentos no gold. En v2 N1 se calcula **por hecho**:

1. Cada hecho `H#` tiene una lista de **fragmentos de evidencia** del corpus (`evidence_pilot.json`, generada con
   `evidence_build.py` por búsqueda de ID de ATT&CK y texto en `chunks.jsonl`; el evaluador verifica las entradas `alt` y
   `alt-parcial`). Cada fragmento es:
   - `gold`: está en `gold_point_ids` de la pregunta;
   - `alt`: no es gold pero sostiene el hecho por sí solo (p. ej. el documento del software en lugar del del grupo);
   - `alt-parcial`: lo sostiene de forma indirecta o genérica (p. ej. la mitigación del padre T1059 para una sub-técnica).
2. `llegó` por hecho y respuesta RAG (`evidence_check.py`, automático): **SI** si llegó un fragmento gold; **ALT** si solo llegó
   una alternativa; **ALT-P** si solo llegó una parcial; **NO** si ninguno.
3. **N1 de la pregunta**: **NINGUNA** (ningún hecho con SI/ALT), **PARTE** o **TODA**, con la fracción *hechos que llegaron ÷
   hechos totales* y el rango del mejor fragmento de evidencia. En preguntas nulas N1 = N/A.
4. **ALT-P no cuenta como "llegó"** por defecto (criterio estricto). El evaluador puede aceptarla justificándolo; entonces el
   hecho se trata como ALT para E1 frente a E2.
5. `hit@k` y `recall@k` por gold se conservan como columnas secundarias. **No son el veredicto**: un hit gold no implica
   suficiencia (p09: hit = SI pero llegaron 2 de 6 hechos) y un fallo gold no implica que no llegara evidencia (p05: gold 0/3,
   pero H2 y H3 llegaron como ALT).
6. N1 alimenta el diagnóstico: un hecho omitido, incorrecto o negado con `llegó = NO` → E1; con `SI`/`ALT` → E2.

**Resultado en el piloto** (`n1_v2.json`): p01 NINGUNA (0/5; H5 solo como ALT-P) · p02 PARTE (1/5) · p03, p04, p06, p07 TODA ·
p05 PARTE (2/4, ambos ALT) · p08 NINGUNA (0/3) · p09 PARTE (2/6) · p10–p13 N/A.

### 4.2 Citas: reglas de decisión (por afirmación de `hecho`, solo modo RAG)

- **Soporte = el fragmento expresa la relación**, no solo nombra las entidades. Dos nombres en la misma lista no sostienen
  "A usa B" (p05, "APT29 usa Mimikatz" → `SIN-RESPALDO`).
- **Alcance de la cita.** Una cita [n] cubre las afirmaciones de su misma frase o viñeta. Repetirla en una "respuesta final"
  cuenta como la misma cita.
- **Cabecera cortada por el chunking.** Si el contenido sostiene la afirmación aunque falte la etiqueta (M1054 en p09), cuenta
  como sostenida.
- **Se revisan siempre**, también en respuestas incorrectas.
- **Las abstenciones no se califican en citas.** Si el hecho sí llegó, es un problema de generación (`ABS-E` → E2). La cita
  que acompañe a una abstención se anota en `nota` pero no entra en N3 ni en las métricas.
- **`SIN-CITA` no cuenta como respaldada** en N3 (criterio de v1.1), pero se reporta aparte para no confundirla con una
  afirmación sin base.

### 4.3 Métricas de recuperación y citas

| Métrica | Definición | Nivel |
|---|---|---|
| N1 por pregunta | NINGUNA / PARTE / TODA + hechos llegados ÷ hechos totales | pregunta |
| Cobertura de recuperación | Σ hechos llegados ÷ Σ hechos (respondibles) | agregado |
| Precisión de citas | afirmaciones de hecho `SOSTENIDA` ÷ afirmaciones de hecho (= base de N3) | respuesta / agregado |
| Cobertura de citas | hechos cubiertos por una afirmación `CORRECTA` y `SOSTENIDA` ÷ hechos totales | respuesta / agregado |
| `SIN-RESPALDO`, `CITA-X`, `SIN-CITA` | conteo de cada uno, por separado | agregado |

La cobertura de citas es la métrica comparable con la precisión/recall de citas de ALCE (§7).

## 5. Comparación con y sin RAG

### 5.1 Qué se compara y qué no

Ambos modos usan el mismo modelo y configuración. La vara es la misma `reference`, **cerrada al corpus**. Por eso la
comparación mide fidelidad a esa referencia y abstención; **no** mide veracidad general. Una afirmación cierta en el mundo pero
ausente de la referencia es `FUERA_REF`: se cuenta y se reporta, no se premia ni se penaliza, y no se verifica contra fuentes
externas. La diferencia de N2 entre modos **deja de ser el titular** (mezclaba fidelidad, abstención y respaldo, y penalizaba
al LLM por construcción). Las cuatro lecturas separadas se derivan de `Afirmaciones` y `Hechos` sin calificación adicional:

| Lectura | Métrica | Modos | Pregunta que responde |
|---|---|---|---|
| **A. Fidelidad a la referencia** | cobertura de hechos (C ÷ H) y proporción de afirmaciones `INCORRECTA` | ambos | ¿Dijo lo que ATT&CK dice y cuánto contradijo? |
| **B. Abstención** | estado en la parte respondible y en la no respondible | ambos | ¿Se abstuvo cuando debía y cuando no debía? |
| **C. Respaldo documental** | precisión y cobertura de citas, `SIN-RESPALDO`/`CITA-X`/`SIN-CITA` | solo RAG | ¿Lo dicho está sostenido por lo recibido? |
| **D. Fuera de referencia** | conteo de afirmaciones `FUERA_REF` | ambos | ¿Qué más dijo? (sin juicio de valor) |

C no es una comparación: el LLM no recibe fragmentos, así que su respaldo es N/A por construcción y no se reporta como falla.

### 5.2 Lectura B: estados de abstención

En la **parte respondible** (H > 0): `responde` (C = H, sin `ABS-E`) · `responde parcial` · `responde parcial + ABS-E` ·
`se abstiene (ABS-E)` (C = 0 y niega lo que la referencia contiene) · `no cubre` (C = 0 sin abstenerse). En la **parte no
respondible**: `se abstiene` · `responde (NO-ABS)` · `no la aborda`. Se reporta el conteo de cada estado por modo; las dos
tasas de interés son la abstención errónea (`ABS-E`) y la respuesta sin base (`NO-ABS`).

### 5.3 Reporte

- Tabla **emparejada por pregunta** (ambos modos) con cobertura, `INCORRECTA`, estado de abstención, `FUERA_REF`, N2 y N3, más
  totales descriptivos por modo.
- **Sin pruebas de significancia**: con tan pocas preguntas no las sostendrían; se reportan conteos y los casos concretos que
  explican cada diferencia.
- Se permite concluir, p. ej., "frente a la referencia, el RAG cubre X de Y hechos y se abstiene en N de M partes sin
  respuesta". No se permite concluir "el RAG es más veraz que el LLM".
- Con los 8 casos calificados por afirmación, la cobertura total es **4/18 en ambos modos**, pero distribuida distinto (p05 y
  p06 favorecen al RAG; p01 y p09 al LLM, este último con `INCORRECTA` y `NO-ABS`). La lectura del piloto "el RAG duplica el N2
  del mismo LLM" se sustituye por A–D.

### 5.4 Herramientas

| Archivo | Función | Modifica el piloto |
|---|---|---|
| `evidence_build.py` → `evidence_pilot.json` | hechos y fragmentos de evidencia por pregunta | no |
| `evidence_check.py <corrida>` → `<corrida>/n1_v2.json` | `llegó` por hecho y N1 de cada respuesta RAG | solo agrega un archivo nuevo |
| `comparar_modos.py [csv]` | deriva N2, N3 y las lecturas A–D desde un CSV de afirmaciones | no escribe |
| `afirmaciones_ejemplos.csv` | 27 afirmaciones de 8 respuestas calificadas; plantilla y prueba del cálculo | — |
| `build_calificacion_v2.py <corrida>` | genera `v2/calificacion_v2_piloto.xlsx`; **no sobrescribe** un libro existente | no |

**Plantilla Excel.** Hojas `Guia`, `Respuestas` (una fila por pregunta × modo; lo derivado en verde), `Afirmaciones` (donde se
califica a mano, con listas desplegables y columna de chequeo), `Hechos`, `Contextos`, `Resumen` (lecturas A–D y alertas) y
`Config`. Con `--demo` genera `calificacion_v2_DEMO.xlsx`, relleno con los ejemplos y una columna "esperado". Las fórmulas se
verificaron con un motor independiente y los valores guardados por Excel en una copia (`calificacion_v2.xlsx`) coinciden con
los esperados en las 8 respuestas.

## 6. Limitaciones del corpus y del sistema (v1.1)

### 6.1 Nivel N0 (corpus)

1. **Solo el dominio Enterprise** (v19.2). Mobile e ICS no están ingestados → preguntas sobre T14xx (Mobile) o T08xx (ICS) son
   no respondibles por construcción (p10, p11).
2. **Solo contenido oficial de ATT&CK**: descripciones, relaciones grupo↔técnica↔software↔mitigación↔detección y ejemplos de
   procedimiento. No hay estadísticas de incidencia, precios, recomendaciones de productos, normas externas (PCI, ISO),
   historial de versiones de herramientas ni noticias.
3. **Idioma**: todo el corpus está en inglés; las preguntas en español se responden con evidencia en inglés.
4. **Ejemplos de procedimiento truncados a 25 por técnica** (`MAX_PROCEDURE_EXAMPLES=25`). Para técnicas muy usadas, la lista
   "quién la usa" está incompleta a propósito.
5. **Chunking por caracteres (1.200, solape 150)**: listas largas quedan repartidas en varios fragmentos; el RAG solo recibe 5.
6. **Defecto de chunking detectado (2026-09-21)**: en documentos largos algunos fragmentos repiten el texto de solape dos
   veces. Ejemplos verificados: `G0032` chunk 4/6, `G0016` chunk 3/4, `M1038` chunks 4–5/5, `S0154` chunk 3/4, `T1110.003`
   chunk 4/9. Efecto: ruido y texto truncado a mitad de línea dentro del contexto; no impide la recuperación. **Decisión**: el
   corpus se congeló tal cual para el piloto (cambiarlo habría invalidado las comparaciones). La corrección en
   `app/rag/chunking.py` más reingesta (~60 min en CPU) queda para antes de la siguiente corrida (§8).
7. **Foto temporal**: ATT&CK v19.2 descargado el 2026-09-12; nada posterior existe en el corpus.
8. **Dos tipos de pregunta no respondible**: (a) sin respuesta en ninguna fuente (p08 %, p09 producto recomendado, p12 "más usada
   en 2026", p13 T1059.099 inexistente) y (b) fuera del corpus pero existentes en el mundo real (p10 Mobile, p11 ICS, precio de
   p04 y posiblemente p06). En (b) el modo LLM puede acertar desde su entrenamiento; en v2 eso se reporta como `FUERA_REF`.

### 6.2 Limitaciones del sistema detectadas durante el piloto

- **Truncado de la respuesta.** `LLM_NUM_PREDICT=1024` cortó a mitad la respuesta de p01 en modo LLM (`completion_tokens = 1024`).
  Se señala con `TRUNC` y se califica tal cual.
- **Ventana de contexto.** Con `top_k=5` el prompt RAG ocupó 1.201–1.854 tokens (máx. 1.931 con la respuesta, 47 % de 4.096). Si
  se sube `top_k` (≈350 tokens por fragmento) hay que subir `LLM_NUM_CTX`: Ollama descarta el inicio del prompt sin error cuando
  no cabe, y se perderían las instrucciones del sistema.
- **Embeddings.** `granite-embedding:30m` trunca a 512 tokens (un fragmento de 1.200 caracteres ≈ 300–400, cabe) y está
  orientado al inglés: con preguntas en español la similitud se deja llevar en parte por el idioma (en una prueba, un texto en
  español sin relación puntuó más que uno en inglés sobre otro tema de ATT&CK). Relevante para el efecto del idioma.
- **Recuperación híbrida no determinista en empates (2026-09-22).** En p01, dos fragmentos con el mismo score RRF (0,2500) en
  el rango 5 (`S0393` y `T1059.010`) se ordenan de forma arbitraria (3 veces uno, 2 veces el otro en 5 llamadas a `/retrieve`).
  Consecuencias: la traza (`traces.jsonl`) es el **único registro válido** de lo que el LLM recibió; las columnas automáticas
  nunca se corrigen a mano; si un gold queda en la frontera empatada, N1 y E1/E2 pueden cambiar entre ejecuciones.
  `run_pilot.py --check-ties <corrida>` detecta estos casos (`ties.json`). En la corrida `20260922_064359` hay empate en la
  frontera en p01, p04 y p12, **ningún gold en la frontera** → los veredictos N1 de esa corrida son estables. Es un hallazgo del
  sistema bajo prueba, no del protocolo; se reporta como limitación de reproducibilidad (punto de mejora: desempate
  determinista en `vectorstore.search`, p. ej. por `point_id`).

## 7. Validación y posicionamiento

### 7.1 Matriz comparativa ampliada

`matriz_comparativa_evaluacion_RAG_v3.xlsx` (la original queda intacta) compara RAGAS, RAGChecker, ARES, FActScore, RefChecker
y, añadidos, **ALCE** (Gao et al., EMNLP 2023) y **CiteEval** (Xu et al., ACL 2025), ambos leídos en sus PDF
locales (`ALCE.pdf` y `CiteEval.pdf` en `CAPSTON/`, versiones de los proceedings; cifras contrastadas el 2026-10-19).

| | ALCE | CiteEval |
|---|---|---|
| Unidad | enunciado (recall) y cita (precisión) | enunciado (oración) |
| Citas | *citation recall* (los pasajes citados implican el enunciado, NLI binario, sin cita = 0) y *citation precision* (cada cita es relevante) | escala 1–5 contra **todo el contexto recuperado**, con acciones de edición (añadir/quitar citas); enunciados no basados en recuperación = "no aplica" |
| Validación humana | 100 ejemplos; kappa 0,698 (recall) y 0,525 (precisión) | 1.200 respuestas anotadas; α de Krippendorff 0,980 (atribución de contexto) y 0,774 (calificación de citas) |
| Limitaciones declaradas | exactitud del NLI; no detecta apoyo parcial; sin multi-hop | no evalúa recuperación de punta a punta; sin medir impacto en usuarios; unidad = oración |

### 7.2 Diferenciación de la contribución

Ya no se afirma que "las citas no se han estudiado". La diferenciación es:

1. **Diagnóstico encadenado.** ALCE y CiteEval puntúan citas dado lo recuperado; este protocolo ubica *dónde* falló (corpus,
   recuperación, generación o citas) y admite varios fallos por respuesta.
2. **Referencia por hechos con cobertura del corpus.** Distingue "no estaba en el corpus", "estaba y no llegó" y "llegó y no se
   usó". En el texto de ALCE no se encontró evaluación de abstención ni de cobertura del corpus por pregunta (a verificar).
3. **Dominio y condición.** Ciberseguridad (MITRE ATT&CK), preguntas en español e inglés, modelo local pequeño, protocolo
   manual pensado para convertirse en un módulo de auditoría continua.

Lo que se reutiliza y debe citarse: la unidad de enunciado y la distinción entre cita que sostiene y que no (ALCE); juzgar
contra el contexto completo y no solo lo citado (CiteEval), que corresponde a distinguir `SIN-CITA` de `CITA-X`.

### 7.3 Validación de consistencia **[pendiente]**

- **pendiente**

## 8. Corrida reproducible **[pendiente]**

Requisitos fijados antes de la siguiente corrida:

1. Corregir el solape duplicado del chunking (`app/rag/chunking.py`) y reingerir.
2. Comprobar que la ingesta esté completa (puntos esperados frente a la colección).
3. Proteger las calificaciones: regenerar el Excel no debe sobrescribirlas. *Cubierto en parte*: `build_calificacion_v2.py` se niega
   a sobrescribir. `run_pilot.py --rebuild-xlsx` del piloto sigue sobrescribiendo la calificación manual (v1.1 §5).
4. Impedir que una reanudación (`--resume`) mezcle configuraciones.
5. Conservar la versión exacta del corpus (`manifest`), los textos gold y los límites de generación (`LLM_NUM_CTX`, `LLM_NUM_PREDICT`).
6. Mantener intacto el piloto original.
7. Desempate determinista en la recuperación (§6.2), si se decide corregirlo antes de la corrida.

**Conjunto nuevo de preguntas [pendiente]:** primero se cierra la rúbrica; después se propone un conjunto equilibrado por
cobertura del corpus (completa / parcial / nula) y viable de calificar con la tabla por afirmación. No se amplía el inglés salvo
que se estudie el idioma; en ese caso, preguntas equivalentes en ambos idiomas.

Ejecución del piloto (referencia, v1.1):

```bash
cd D:/DS_USFQ/CAPSTON/RAG
python eval/pilot/run_pilot.py
python eval/pilot/run_pilot.py --resume eval/pilot/results/<timestamp>
python eval/pilot/run_pilot.py --check-ties eval/pilot/results/<timestamp>
```

## 9. Resultados del piloto (corrida `20260922_064359`)

13 preguntas × 2 modos, una calificación manual por respuesta con la rúbrica v1.1 (un evaluador).

| Métrica (v1.1) | RAG | LLM |
|---|---|---|
| N2 promedio (0–2) | 1,23 (62 %) | 0,54 (27 %) |
| N3 promedio (0–2, 7 respuestas con afirmaciones) | 1,71 (86 %) | N/A |
| N1 hit@5 · recall@5 (9 respondibles) | 6/9 (67 %) · 56 % | N/A |
| OK / E0 / E1 / E2 / E3 | 7 / 0 / 5 / 1 / 0 | 2 / 3 / 0 / 8 / 0 |

Lectura v1.1: el RAG duplica el N2, con ventaja sobre todo en abstención (4/4 en nulas frente a 1/4); si el gold no llega, RAG =
LLM; E1 es el error dominante del RAG (5 de 6); el RAG es conservador (se abstuvo en p01, p06, p08, p09). **Esta lectura queda
superada por §5**: la diferencia de N2 no demuestra mejora de precisión factual, y la nota única esconde causas distintas.

**Recalificación v2 de 8 respuestas** (`ejemplos_calificados_v2.md`, calificadas por Claude, pendientes de revisión del evaluador):

| Caso | Modo | N2 v1.1 → v2 | N3 v1.1 → v2 | Diagnóstico v1.1 → v2 | Alertas v2 |
|---|---|---|---|---|---|
| p01 | RAG | 0 → 0 | N/A → N/A | E1 → E1 | CRITICA |
| p01 | LLM | 1 → 1 | N/A → N/A | E2 → E2 | CRITICA, TRUNC |
| p05 | RAG | 1 → 1 | 1 → 1 | E1 → E1+E2+E3 | RESPALDO |
| p05 | LLM | 0 → 0 | N/A → N/A | E2 → E2 | CRITICA |
| p06 | RAG | **0 → 1** | 2 → 2 | E2 → E2 | CRITICA |
| p06 | LLM | 0 → 0 | N/A → N/A | E2 → E2 | CRITICA |
| p09 | RAG | 0 → 0 | 2 → 2 | E1 → E1+E2 | CRITICA |
| p09 | LLM | **0 → 1** | N/A → N/A | E2 → E0+E2 | CRITICA |

Cobertura total de hechos en esas 8 respuestas: **4/18 en RAG y 4/18 en LLM**. Las dos diferencias de N2 respecto de v1.1 (p06 RAG,
p09 LLM) son consecuencia de separar cobertura y veredicto (§3.4), no errores.

**Casos ilustrativos.**

- **p05 (RAG):** "APT29 usa Mimikatz" es correcta pero `SIN-RESPALDO` (el fragmento 1 contiene ambos nombres en la misma lista, no
  la relación). "Mimikatz implementa T1550.003" está sostenida. Faltan Golden Ticket (llegó como ALT) y Silver Ticket (no llegó).
- **p09 (RAG):** niega las mitigaciones (`ABS-E`) aunque el fragmento 5 traía M1054 y M1047; la abstención sobre el producto
  comercial es correcta.
- **p01 (RAG):** la recuperación no trajo las mitigaciones (0/5; el M1042 del padre T1059 es ALT-P) → E1. En LLM la respuesta
  está truncada y niega que ATT&CK liste mitigaciones (`INC`).
- **p06 (RAG):** el gold llegó, nombra bien 2 de 3 sub-técnicas y concluye "no se puede determinar" (`ABS-E`) → E2.

Advertencias: muestra pequeña (13 preguntas), un solo evaluador, una sola corrida.

## 10. Casos ambiguos de v1.1 y su resolución en v2.2

| Caso | Pregunta(s) | Resolución en v1.1 | Resolución en v2.2 |
|---|---|---|---|
| Gold parcial: N1 = SI pero falta un gold | p02, p09 | E1 o E2 según dónde estaba lo omitido | N1 por evidencia y `llegó` por hecho (§4.1) |
| Evidencia alternativa en fragmentos no gold | p05 | Calificar normal, anotar | `alt` / `alt-parcial` en la tabla de evidencia (§4.1) |
| Correcto sin soporte en el contexto | p05 | N3 baja | `vs_ref=CORRECTA` + `respaldo=SIN-RESPALDO` (§3.2) |
| LLM correcto fuera de la referencia | p10, p11 (y precio de p04) | Calificar contra la referencia, anotar | `FUERA_REF` / `NO-ABS`, reportado aparte (§3.3, §5.1) |
| Nombre "E0-corpus" en modo LLM | p10, p11, p13 | Se interpreta como "no se abstuvo" | Renombrado `E0-no-abstencion` (§3.5) |
| N3 ante abstención | p08, p10–p13 | N/A, nunca 0 | N/A; las abstenciones no se califican en citas (§4.2) |
| Respuesta truncada por límite de tokens | p01 LLM | Calificar tal cual, anotar | Indicador `TRUNC` y alerta (§3.3, §3.6) |

## 11. Entregables y estado

| # | Entregable | Estado |
|---|---|---|
| 1 | RQ y sub-preguntas (§1) | v2.2 |
| 2 | Matriz comparativa con ALCE y CiteEval | hecha: `matriz_comparativa_evaluacion_RAG_v3.xlsx` |
| 3 | Piloto: preguntas, trazas, calificación, tabla de diagnósticos y casos ambiguos | hecho (v1.1) y recalificación v2 de 8 respuestas |
| 4 | Rúbrica v2: calificación por afirmación, N1 por evidencia, comparación con y sin RAG | hecha (borrador) |
| 5 | Plantilla Excel v2 y scripts de apoyo | hechos (`v2/`, `*.py`) |
| 6 | Validación de consistencia | pendiente (§7.3) |
| 7 | Corrida reproducible y conjunto nuevo de preguntas | pendiente (§8) |
| 8 | Propuesta de evaluación final | pendiente |

---

## Anexo A. Rúbrica v1.1 original (para comparabilidad del piloto)

Se conserva tal cual para que la calificación hecha en `calificacion.xlsx` siga siendo interpretable. Una fila por pregunta × modo.

| Nivel | Valores | Regla |
|---|---|---|
| N0 corpus (auto) | completa / parcial / nula | Viene del diseño de la pregunta |
| N1 recuperación (auto, solo RAG) | SI / NO + rango | Algún fragmento gold entre los top-k |
| N2 respuesta (manual) | 2 / 1 / 0 | 2 correcta y completa · 1 a medias · 0 incorrecta o inventada. Nula: 2 = se abstuvo, 0 = inventó. Parcial: 2 = responde lo disponible y se abstiene del resto · 1 = responde lo disponible pero inventa el resto · 0 = erra lo disponible |
| N3 citas (manual, solo RAG) | 2 / 1 / 0 / N/A | 2 toda afirmación citada y sostenida · 1 alguna sin cita o cita que no la sostiene · 0 sin citas o equivocadas · N/A si se abstuvo |
| Diagnóstico (manual) | OK / E0-corpus / E1-recuperacion / E2-generacion / E3-citas | **Primer eslabón que falló**: E0 no estaba y no se abstuvo → E1 estaba pero no llegó → E2 llegó y aun así N2<2 → E3 N2=2 pero N3<2 |

Modo LLM: solo N2 y diagnóstico (OK / E0-corpus / E2-generacion).

**Reglas de aplicación (v1.1 §3.1).**

- *Fuente de verdad.* La `reference` es la vara de **ambos** modos; "tiene respuesta" es una decisión del diseño (N0), no una
  afirmación sobre lo que el modelo sabe.
- *N1.* hit@k binario por pregunta (cuenta 1 si llega al menos un gold); se reporta además recall@k. N1 es una aproximación: la
  respuesta puede estar en un fragmento no gold; no se corrige N1, se anota en el comentario.
- *N3.* N/A solo cuando la respuesta no hace ninguna afirmación basada en los fragmentos (abstención total) y en todas las filas
  LLM; abstención parcial: se califica N3 sobre la parte respondida; afirmación correcta sin fragmento que la sostenga: N2 alto,
  N3 baja; el promedio N3 excluye N/A.
- *Diagnóstico.* OK solo si N2 = 2 y N3 ∈ {2, N/A}; E3 exige N2 = 2 y N3 numérico < 2; gold parcial: E1 si lo que falta estaba en
  el gold que no llegó, E2 si estaba en lo que sí llegó; abstención errónea: N2 = 0, N3 = N/A, E2.
- *Modo LLM.* E1 y E3 imposibles; E0 = pregunta sin respuesta según la referencia y el modelo no se abstuvo; E2 = la pregunta tiene
  referencia y N2 < 2 (suele significar que no lo sabía o lo recordó mal); RAG vs LLM se compara con N2, no con el conteo de E2;
  respuesta cierta en el mundo real pero fuera de la referencia: se califica contra la referencia y se anota.

## Anexo B. Correspondencia v1.1 → v2

| v1.1 | v2 |
|---|---|
| N2 manual 0/1/2 | derivado de `Afirmaciones` + `Hechos` (§3.4); misma escala |
| N3 manual 0/1/2/N/A | derivado (§3.4); `SIN-R` y `CITA-X` se distinguen |
| "correcto sin soporte" (p05) | `vs_ref=CORRECTA` + `respaldo=SIN-RESPALDO` |
| abstención errónea (p09) | `tipo=abstencion` + `vs_ref=INCORRECTA` → `ABS-E` |
| E0-corpus en modo LLM | `E0-no-abstencion` |
| primer eslabón | derivado de la lista de causas |
| "correcto fuera de la referencia" | `FUERA_REF`, reportado aparte |
| N1 = algún gold | N1 por evidencia (NINGUNA/PARTE/TODA) |

## Anexo C. Archivos del proyecto (`RAG/eval/pilot/` salvo indicación)

| Archivo | Contenido |
|---|---|
| `protocol.md` | Protocolo v1.1 (intacto) |
| `protocol_v2.md` | Borrador v2 (intacto desde esta consolidación) |
| `protocol_v2.2.md` | Este documento |
| `questions.jsonl`, `results/20260922_064359/` | Preguntas y corrida del piloto (intactos) |
| `ejemplos_calificados_v2.md`, `afirmaciones_ejemplos.csv` | Ocho respuestas calificadas por afirmación |
| `evidence_build.py`, `evidence_pilot.json`, `evidence_check.py` | Tabla de evidencia y cálculo de N1 |
| `comparar_modos.py`, `build_calificacion_v2.py`, `v2/*.xlsx` | Cálculo de lecturas y plantilla Excel |
| `resumen_reunion.md` | Resumen de una página para la reunión |
| `../../../matriz_comparativa_evaluacion_RAG_v3.xlsx` | Matriz con ALCE y CiteEval (carpeta `CAPSTON`) |
