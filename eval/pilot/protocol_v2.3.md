# Evaluación diagnóstica de un RAG local sobre MITRE ATT&CK — protocolo v2.3 (rúbrica congelada)

**Qué es este documento.** Versión congelada de la rúbrica, resultado de las decisiones del director del 2026-10-29. Sustituye a
`protocol_v2.2.md` como referencia para la corrida reproducible (§8) y el documento final. `protocol.md` (v1.1), `protocol_v2.md`,
`protocol_v2.2.md`, `questions.jsonl` y la corrida `20260922_064359` siguen intactos.

**Estado (2026-10-30).** §1–§7 cerrados. §8: código de la corrida reproducible hecho y probado sin servicios; faltan la reingesta,
el conjunto nuevo de preguntas y la corrida. §9 (propuesta de evaluación final) se redacta tras la corrida.

| Versión | Fecha | Qué incorpora |
|---|---|---|
| v1 | 2026-09 | Rúbrica N0–N3 de una nota por nivel; piloto de 13 preguntas × 2 modos |
| v1.1 | 2026-09-25 | Reglas de aplicación, limitaciones del sistema, resultados y casos ambiguos del piloto |
| v2 (borrador) | 2026-10-12 | Calificación por afirmación; N1 por evidencia; comparación con y sin RAG; alertas; plantilla Excel |
| v2.2 | 2026-10-19 | Consolidación; matriz con ALCE/CiteEval; plan de validación y de corrida reproducible |
| **v2.3** | 2026-10-30 | **Rúbrica congelada** (decisiones D1–D8); validación con segundo evaluador (§7.3); RQ reformulada; matriz v4 con RGB; módulo de auditoría pasa a trabajo futuro |

Alcance acordado con el director: **evaluar y diagnosticar** las respuestas. El proyecto no es una optimización del RAG.

---

## 0. Decisiones que congelan la rúbrica (director, 2026-10-29)

| # | Decisión | Regla en este documento |
|---|---|---|
| D1 | `ALT-P` no cuenta como "llegó" | §4.1, punto 4 |
| D2 | `CORRECTA` solo si la afirmación **enuncia** el hecho de la referencia; si no, `FUERA_REF` | §3.2, regla de enunciación |
| D3 | Un hecho que llegó y la respuesta niega → `ABS-E` + `E2` | §3.3 y §3.5 |
| D4 | N2 y N3 sin topes | §3.4 |
| D5 | Alertas solo como reporte | §3.6 |
| D6 | Corregir el desempate de la recuperación antes de la corrida | §8 |
| D7 | La consistencia se mide con el segundo evaluador; el juez LLM es solo contraste | §7.3 |
| D8 | El módulo de evaluación y auditoría continua queda como trabajo futuro | §10 |

Observaciones del director sobre el posicionamiento, incorporadas en §1 y §7: RAGChecker ya atribuye recuperador y generador por
afirmación, así que no se presenta "localizar el origen de los errores" como novedad; la contribución es la cobertura del corpus por
pregunta, varios fallos por respuesta y las citas dentro de esa cadena. Se añade RGB (Chen et al., 2024) a la matriz.

## 1. Pregunta de investigación y sub-preguntas

> ¿Permite un protocolo de evaluación manual por afirmación, que registra la cobertura del corpus por pregunta y encadena
> recuperación, generación y citas, diagnosticar de forma consistente los fallos (varios por respuesta) de un sistema RAG local
> sobre MITRE ATT&CK?

| | Sub-pregunta | Nivel | Cómo se responde |
|---|---|---|---|
| RQ1 | ¿Existía en el corpus la información necesaria (total, parcial, nula)? | N0 corpus | Diseño de las preguntas con referencia verificada en `chunks.jsonl` |
| RQ2 | ¿La recuperación trajo la evidencia necesaria: ninguna, parte o toda? | N1 recuperación | Automático por hecho, aceptando evidencia alternativa (§4.1) |
| RQ3 | Dado el contexto, ¿cada afirmación es correcta, completa y fiel a la referencia? | N2 generación | Calificación manual por afirmación; N2 derivado (§3) |
| RQ4 | ¿Cada afirmación está ligada a una cita cuyo fragmento la sostiene? | N3 citas | Calificación manual por afirmación; N3 derivado (§3, §4.2) |
| RQ5 | ¿En qué se diferencian el mismo modelo con y sin recuperación, frente a una referencia común? | comparativo | Cuatro lecturas separadas (§5) |
| RQ6 | ¿El protocolo es consistente entre evaluadores? | validación | Acuerdo con un segundo evaluador independiente (§7.3) |

Cambio respecto de v2.2: la RQ deja de decir "localizar el origen de los errores" (RAGChecker ya lo hace por afirmación) y RQ6 se
responde con el segundo evaluador, no con re-calificación propia ni con juez LLM. Resultado secundario (no en la RQ): efecto del
idioma de la pregunta (9 es / 4 en en el piloto).

## 2. Diseño del piloto (v1.1, sin cambios)

Sistema bajo prueba: RAG genérico de `RAG/` (qwen3:4b-instruct + granite-embedding:30m + Qdrant, corpus MITRE ATT&CK
Enterprise v19.2).

- 13 preguntas en `questions.jsonl`: 5 completas, 4 parciales, 4 no respondibles; 9 en español, 4 en inglés.
- Cada pregunta lleva `gold_point_ids` (fragmentos exactos de `data/chunks.jsonl` con la respuesta), una `reference` redactada
  **solo** a partir de esos fragmentos y, si aplica, la `unanswerable_part` verificada como ausente.
- Configuración fija: recuperación `hybrid`, `top_k=5`, `temperature=0`, `think=false`, modelo por defecto (guardada en
  `results/<run>/config.json`). Límites del `.env`: ventana `LLM_NUM_CTX=4096` (prompt + respuesta) y respuesta máxima
  `LLM_NUM_PREDICT=1024`. Con `temperature=0` la decodificación es *greedy*.
- Cada respuesta se guarda íntegra (`traces.jsonl`): respuesta, contextos con `point_id` y `score`, prompt exacto, tokens y tiempos.

## 3. Qué se califica (rúbrica congelada)

Una respuesta se descompone en **afirmaciones atómicas** (máx. ≈6; si hay más, las que sustentan la referencia). Cada afirmación
se juzga en **dos ejes independientes**:

- **Corrección** frente a la `reference`, que es la misma para ambos modos. La cobertura del corpus (N0) es la condición de
  referencia: que algo no esté en el corpus no lo hace falso.
- **Respaldo** frente a los fragmentos que el sistema recibió (solo modo RAG).

Una respuesta puede tener varios problemas a la vez; se registran todos. Se distinguen tres situaciones que la nota única de v1.1
mezclaba: **incorrecta** (contradice la referencia), **incompleta** (omite hechos de la referencia) y **correcta pero sin
respaldo** en los fragmentos recibidos.

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

**Reglas de decisión (congeladas).**

- **Regla de enunciación (D2).** `CORRECTA` solo si la afirmación **enuncia** el hecho `H#` que se le asigna: nombra el mismo
  objeto y la misma relación que la referencia. Una afirmación que lo cubre de forma indirecta, parcial o con otro nombre es
  `FUERA_REF` (no enuncia) o `INCORRECTA` (lo contradice). Ejemplos del piloto: "Políticas de grupo para limitar el acceso a
  PowerShell" no enuncia *M1026 Privileged Account Management* → `FUERA_REF` (p01 LLM); "T1566.001 es Spear Phishing Email" nombra
  mal *Spearphishing Attachment* → `INCORRECTA` (p02 LLM); "los pasajes mencionan SPF, DKIM y DMARC" sí enuncia *M1054 Software
  Configuration (SPF, DKIM, DMARC)* → `CORRECTA` (p09 RAG). Cada `CORRECTA` lleva su `hecho_ref`; una `CORRECTA` sin `hecho_ref`
  solo es válida en preguntas nulas (H = 0).
- **Abstención vs. afirmación de ausencia.** `abstencion` = el modelo dice que *el contexto o él no tiene* la información ("los
  pasajes no dicen…", "no puedo determinar…"). Una afirmación sobre la fuente ("ATT&CK no documenta…", "no hay mitigaciones") es
  un `hecho` y puede ser `INCORRECTA`. Criterio operativo: si el sujeto es la fuente (ATT&CK, MITRE) es hecho; si es el contexto o
  el propio modelo, abstención.
- **Parte no respondible.** Una `abstencion` con `zona=no_resp` no enuncia ningún hecho de la referencia, por lo que por D2 es
  `FUERA_REF` y no cuenta para N2; se registra como abstención debida en la lectura B (§5.2) y no genera código. Un `hecho` con
  `zona=no_resp` ("MITRE no recomienda ningún producto comercial") es `FUERA_REF` + `NO-ABS`.
- **Listas cerradas.** Los elementos extra que la referencia no incluye son `FUERA_REF` (se reportan aparte como extras), no
  `INCORRECTA`; solo se marca `INCORRECTA` lo que contradice la referencia. En modo RAG un extra además recibe `respaldo`.
- **`llegó`** se determina leyendo los fragmentos recibidos (no solo `gold_points_found`), para registrar evidencia alternativa.

Fuera de la tabla: filas `OMISION` por cada `H#` de la referencia que ninguna afirmación `CORRECTA` cubre, e indicador `TRUNC`
por respuesta si `completion_tokens` alcanza el límite (`LLM_NUM_PREDICT`).

### 3.3 Códigos de problema (derivados de las columnas, no se escriben a mano)

| Código | Se genera cuando |
|---|---|
| `INC` | `tipo=hecho` y `vs_ref=INCORRECTA` |
| `OMI` | existe fila `OMISION` (hecho de la referencia sin cubrir) |
| `ABS-E` | `tipo=abstencion` y `vs_ref=INCORRECTA` (niega algo que la referencia sí contiene; por D3 se registra aunque otra afirmación de la misma respuesta cubra el hecho) |
| `NO-ABS` | `tipo=hecho`, `vs_ref=FUERA_REF` y responde a la `unanswerable_part` o a una pregunta nula (afirma sin base en referencia ni corpus) |
| `SIN-R` | `respaldo=SIN-RESPALDO` (correcta o no) |
| `CITA-X` | `respaldo=CITA-X` |
| `SIN-C` | `respaldo=SIN-CITA` |
| `TRUNC` | respuesta truncada |

Se aplican aunque la respuesta sea incorrecta. Una abstención debida sobre la parte no respondible no genera código. Un
`FUERA_REF` que no responde a la parte no respondible (dato extra, cierto o no) se reporta aparte como "fuera de la referencia";
no cuenta como error.

### 3.4 Notas derivadas (sin topes, D4)

Sea H = nº de hechos de la referencia y C = nº de hechos cubiertos por afirmaciones `CORRECTA`.

**N2 (correcta y completa).**
- H = 0 (pregunta nula): **2** si no hay `NO-ABS`, **0** si lo hay.
- H > 0: **2** si C = H y no hay `INC`, `ABS-E` ni `NO-ABS`; **0** si C = 0; **1** en los demás casos.

**N3 (citas, solo RAG)**, sobre las afirmaciones `hecho`: **N/A** si no hay ninguna (abstención total); **2** si todas son
`SOSTENIDA`; **0** si ninguna lo es; **1** en los demás casos. En modo LLM, N3 es siempre N/A.

N2 y N3 son descriptivos y monótonos: no hay reglas del tipo "si hay X entonces N2 = 0". Los problemas graves no se esconden en la
nota; se señalan con las alertas (§3.6). Por eso p06 (RAG) y p09 (RAG) dan N2 = 1 aunque nieguen parte de lo que cubren.

### 3.5 Diagnóstico: lista de causas

| Etiqueta | Se asigna cuando |
|---|---|
| `E0-no-abstencion` | hay `NO-ABS` |
| `E1-recuperacion` | hay `OMI`, `INC` o `ABS-E` sobre un hecho con `llegó = NO` o `ALT-P` (D1) |
| `E2-generacion` | hay `OMI`, `INC` o `ABS-E` sobre un hecho con `llegó = SI/ALT` (incluye el hecho negado y a la vez cubierto, D3) |
| `E3-citas` | hay `CITA-X`, `SIN-C` o `SIN-R` |
| `OK` | ninguna de las anteriores |

- Una respuesta lleva todas las etiquetas que apliquen (p. ej. `E1 + E2 + E3`). La columna "primer eslabón" se deriva con el orden
  E0 → E1 → E2 → E3 solo para comparar con el piloto v1.1; no es el veredicto.
- **Modo LLM**: no hay recuperación ni fragmentos; `llegó` y `respaldo` no aplican, así que solo pueden aparecer
  `E0-no-abstencion` y `E2-generacion` (aquí significa "no lo sabía o lo recordó mal"). `SIN-R` no se genera.
- Una `INCORRECTA` sin `hecho_ref` (no contradice un hecho concreto, p. ej. un nombre inventado) genera `INC` y alerta, pero no
  entra en E1/E2 porque no tiene `llegó`; en modo LLM cuenta como E2.
- `TRUNC` se reporta como indicador aparte, no como causa E.

### 3.6 Alertas (solo reporte, D5)

La **medición** (afirmaciones → códigos, cobertura, N2, N3) es fija y lleva la versión de la rúbrica. Las alertas señalan qué
respuestas merecen atención; no cambian N2 ni N3 y se reportan en la columna `alertas`:

| Alerta | Se activa cuando la respuesta tiene |
|---|---|
| `CRITICA` | `ABS-E`, `NO-ABS` o `INC` |
| `RESPALDO` | `SIN-R` o `CITA-X` (y `SIN-C`, como aviso menor) |
| `TRUNC` | respuesta truncada |

La política configurable de alertas pensada para el módulo de auditoría continua queda fuera del alcance (§10).

## 4. Recuperación (N1) y citas

### 4.1 N1 por evidencia, no por fragmento gold

1. Cada hecho `H#` tiene una lista de **fragmentos de evidencia** del corpus (`evidence_pilot.json`, generada con
   `evidence_build.py` por búsqueda de ID de ATT&CK y texto en `chunks.jsonl`; el evaluador verifica las entradas `alt` y
   `alt-parcial`). Cada fragmento es `gold` (está en `gold_point_ids`), `alt` (no es gold pero sostiene el hecho por sí solo) o
   `alt-parcial` (lo sostiene de forma indirecta o genérica, p. ej. la mitigación del padre T1059 para una sub-técnica).
2. `llegó` por hecho y respuesta RAG (`evidence_check.py`, automático): **SI** si llegó un fragmento gold; **ALT** si solo llegó
   una alternativa; **ALT-P** si solo llegó una parcial; **NO** si ninguno.
3. **N1 de la pregunta**: **NINGUNA** (ningún hecho con SI/ALT), **PARTE** o **TODA**, con la fracción *hechos que llegaron ÷
   hechos totales* y el rango del mejor fragmento de evidencia. En preguntas nulas N1 = N/A.
4. **`ALT-P` no cuenta como "llegó"** (D1, congelado). Un hecho con solo `ALT-P` se trata como `NO` para E1/E2 y para N1.
5. `hit@k` y `recall@k` por gold se conservan como columnas secundarias. **No son el veredicto**: un hit gold no implica
   suficiencia (p09: hit = SI pero llegaron 2 de 6 hechos) y un fallo gold no implica que no llegara evidencia (p05: gold 0/3,
   pero H2 y H3 llegaron como ALT).
6. N1 alimenta el diagnóstico: un hecho omitido, incorrecto o negado con `llegó = NO/ALT-P` → E1; con `SI`/`ALT` → E2.

**Resultado en el piloto** (`n1_v2.json`): p01 NINGUNA (0/5; H5 solo como ALT-P) · p02 PARTE (2/5) · p03, p04, p06, p07 TODA ·
p05 PARTE (2/4, ambos ALT) · p08 NINGUNA (0/3) · p09 PARTE (2/6) · p10–p13 N/A.

### 4.2 Citas: reglas de decisión (por afirmación de `hecho`, solo modo RAG)

- **Soporte = el fragmento expresa la relación**, no solo nombra las entidades. Dos nombres en la misma lista no sostienen
  "A usa B" (p05, "APT29 usa Mimikatz" → `SIN-RESPALDO`). Si el fragmento expresa la relación textualmente ("G0016 usó ataques de
  tickets Kerberos para movimiento lateral"), es `SOSTENIDA` aunque la afirmación sea `FUERA_REF` (p05, afirmación 2).
- **Alcance de la cita.** Una cita [n] cubre las afirmaciones de su misma frase o viñeta. Repetirla en una "respuesta final"
  cuenta como la misma cita.
- **Cabecera cortada por el chunking.** Si el contenido sostiene la afirmación aunque falte la etiqueta (M1054 en p09), cuenta
  como sostenida.
- **Se revisan siempre**, también en respuestas incorrectas.
- **Las abstenciones no se califican en citas.** Si el hecho sí llegó, es un problema de generación (`ABS-E` → E2).
- **`SIN-CITA` no cuenta como respaldada** en N3, pero se reporta aparte para no confundirla con una afirmación sin base.

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

Ambos modos usan el mismo modelo y configuración. La vara es la misma `reference`, **cerrada al corpus**. Por eso la comparación
mide fidelidad a esa referencia y abstención; **no** mide veracidad general. Una afirmación cierta en el mundo pero ausente de la
referencia es `FUERA_REF`: se cuenta y se reporta, no se premia ni se penaliza. La diferencia de N2 entre modos no es el titular.
Las cuatro lecturas se derivan de `Afirmaciones` y `Hechos` sin calificación adicional:

| Lectura | Métrica | Modos | Pregunta que responde |
|---|---|---|---|
| **A. Fidelidad a la referencia** | cobertura de hechos (C ÷ H) y proporción de afirmaciones `INCORRECTA` | ambos | ¿Dijo lo que ATT&CK dice y cuánto contradijo? |
| **B. Abstención** | estado en la parte respondible y en la no respondible | ambos | ¿Se abstuvo cuando debía y cuando no debía? |
| **C. Respaldo documental** | precisión y cobertura de citas, `SIN-RESPALDO`/`CITA-X`/`SIN-CITA` | solo RAG | ¿Lo dicho está sostenido por lo recibido? |
| **D. Fuera de referencia** | conteo de afirmaciones `FUERA_REF` | ambos | ¿Qué más dijo? (sin juicio de valor) |

### 5.2 Lectura B: estados de abstención

En la **parte respondible** (H > 0): `responde` (C = H, sin `ABS-E`) · `responde parcial` · `responde parcial + ABS-E` ·
`se abstiene (ABS-E)` (C = 0 y niega lo que la referencia contiene) · `no cubre` (C = 0 sin abstenerse). En la **parte no
respondible**: `se abstiene` (abstención debida, `FUERA_REF` sin código) · `responde (NO-ABS)` · `no la aborda`. Las dos tasas
de interés son la abstención errónea (`ABS-E`) y la respuesta sin base (`NO-ABS`).

### 5.3 Resultado del piloto con la rúbrica congelada (26 respuestas, `v2/calificacion_v2.xlsx`, 2026-10-30)

| Lectura | RAG | LLM |
|---|---|---|
| A. Hechos de la referencia cubiertos (÷ 33 respondibles) | 14 (42 %) | 7 (21 %) |
| A. Afirmaciones `INCORRECTA` ÷ afirmaciones de hecho | 19 % | 23 % |
| B. Respuestas con abstención errónea (`ABS-E`) | 3 | 1 |
| B. Respuestas con respuesta sin base (`NO-ABS`) | 0 | 7 |
| C. Precisión de citas | 71 % | N/A |
| C. Cobertura de citas (hechos cubiertos y citados ÷ hechos) | 39 % | N/A |
| C. `SIN-RESPALDO` / `CITA-X` / `SIN-CITA` | 1 / 4 / 1 | N/A |
| D. Afirmaciones `FUERA_REF` | 3 | 33 |
| N2 promedio (descriptivo) | 1,38 | 0,38 |
| N3 promedio (descriptivo, excluye N/A) | 1,50 | N/A |
| Alertas `CRITICA` / `RESPALDO` / `TRUNC` (respuestas) | 5 / 3 / 0 | 12 / 0 / 1 |

Por respuesta (C/H, N2, N3, diagnóstico):

| Pregunta | RAG | LLM |
|---|---|---|
| p01 completa | 0/5, 0, N/A, E1 | 1/5, 1, N/A, E2 (TRUNC) |
| p02 completa | 2/5, 1, 1, E1 E3 | 2/5, 1, N/A, E2 |
| p03 completa | 2/2, 2, 2, OK | 1/2, 1, N/A, E2 |
| p04 parcial | 2/2, 2, 2, OK | 1/2, 1, N/A, E0 E2 |
| p05 completa | 2/4, 1, 1, E1 E2 E3 | 0/4, 0, N/A, E2 |
| p06 parcial | 2/3, 1, 2, E2 | 0/3, 0, N/A, E0 E2 |
| p07 completa | 3/3, 2, 2, OK | 0/3, 0, N/A, E2 |
| p08 parcial | 0/3, 0, 0, E1 E3 | 0/3, 0, N/A, E2 |
| p09 parcial | 1/6, 1, 2, E1 E2 | 2/6, 1, N/A, E0 E2 |
| p10–p13 nulas | 2, N/A, OK (×4) | 0, N/A, E0 (p10, p11) · E0 E2 (p12, p13) |

Lectura: frente a la referencia, el RAG cubre el doble de hechos que el LLM (14 frente a 7 de 33) y nunca responde sin base en las
preguntas y partes no respondibles (0 frente a 7), a costa de abstenerse erróneamente en 3 respuestas donde la evidencia sí llegó.
Donde la recuperación no trajo la evidencia (p01, p08) ambos modos fallan; donde llegó completa (p03, p04, p07) el RAG es
correcto y completo. El LLM añade 33 afirmaciones fuera de la referencia (ciertas o no, no se verifican). Sin pruebas de
significancia: muestra de 13 preguntas, un evaluador principal, una corrida.

### 5.4 Herramientas

| Archivo | Función | Modifica el piloto |
|---|---|---|
| `evidence_build.py` → `evidence_pilot.json` | hechos y fragmentos de evidencia por pregunta | no |
| `evidence_check.py <corrida>` → `<corrida>/n1_v2.json` | `llegó` por hecho y N1 de cada respuesta RAG | solo agrega un archivo nuevo |
| `comparar_modos.py [csv]` | deriva N2, N3 y las lecturas A–D desde un CSV de afirmaciones | no escribe |
| `build_calificacion_v2.py <corrida>` | genera la plantilla Excel; **no sobrescribe** un libro existente | no |
| `v2/calificacion_v2.xlsx` | calificación completa del piloto con esta rúbrica (evaluador principal) | — |
| `v2/calificacion_v2_eval_independent.xlsx` | calificación del segundo evaluador (p01, p05, p06, p09) | — |

**Plantilla Excel.** Hojas `Guia`, `Respuestas` (derivado en verde), `Afirmaciones` (donde se califica a mano), `Hechos`,
`Contextos`, `Resumen` (lecturas A–D y alertas) y `Config` (evaluador, fecha, configuración de la corrida). Las fórmulas se
verificaron con un recálculo independiente en Python sobre las 26 respuestas (2026-10-22 y 2026-10-30): coinciden.

## 6. Limitaciones del corpus y del sistema (v1.1, sin cambios de fondo)

### 6.1 Nivel N0 (corpus)

1. **Solo el dominio Enterprise** (v19.2). Mobile e ICS no están ingestados → preguntas sobre T14xx o T08xx son no respondibles
   por construcción (p10, p11).
2. **Solo contenido oficial de ATT&CK**: no hay estadísticas de incidencia, precios, productos, normas externas ni noticias.
3. **Idioma**: todo el corpus está en inglés; las preguntas en español se responden con evidencia en inglés.
4. **Ejemplos de procedimiento truncados a 25 por técnica** (`MAX_PROCEDURE_EXAMPLES=25`).
5. **Chunking por caracteres (1.200, solape 150)**: listas largas quedan repartidas en varios fragmentos; el RAG solo recibe 5.
6. **Defecto de chunking (2026-09-21)**: en documentos largos algunos fragmentos repiten el texto de solape dos veces (`G0032`
   chunk 4/6, `G0016` 3/4, `M1038` 4–5/5, `S0154` 3/4, `T1110.003` 4/9). No impide la recuperación. El corpus del piloto se
   congeló tal cual; la corrección y la reingesta son parte de §8.
7. **Foto temporal**: ATT&CK v19.2 descargado el 2026-09-12.
8. **Dos tipos de pregunta no respondible**: (a) sin respuesta en ninguna fuente (p08 %, p09 producto, p12, p13) y (b) fuera del
   corpus pero existentes en el mundo real (p10 Mobile, p11 ICS, precio de p04). En (b) el LLM puede acertar desde su
   entrenamiento; se reporta como `FUERA_REF`.

### 6.2 Limitaciones del sistema detectadas durante el piloto

- **Truncado de la respuesta.** `LLM_NUM_PREDICT=1024` cortó la respuesta de p01 en modo LLM. Se señala con `TRUNC`.
- **Ventana de contexto.** Con `top_k=5` el prompt RAG ocupó 1.201–1.854 tokens (47 % de 4.096). Si se sube `top_k` hay que subir
  `LLM_NUM_CTX`: Ollama descarta el inicio del prompt sin error cuando no cabe.
- **Embeddings.** `granite-embedding:30m` trunca a 512 tokens y está orientado al inglés; con preguntas en español la similitud se
  deja llevar en parte por el idioma.
- **Recuperación híbrida no determinista en empates (2026-09-22).** Fragmentos con el mismo score RRF en la frontera del top-k se
  ordenan de forma arbitraria (p01, p04, p12 en el piloto; ningún gold en la frontera, así que los veredictos N1 del piloto son
  estables). La traza es el único registro válido de lo que recibió el LLM. **Se corrige antes de la corrida nueva (D6, §8).**

## 7. Validación y posicionamiento

### 7.1 Matriz comparativa (v4)

`matriz_comparativa_evaluacion_RAG_v4.xlsx` (carpeta `CAPSTON`; v3 y la original quedan intactas) compara RAGAS, RAGChecker,
ARES, FActScore, RefChecker, ALCE, CiteEval y, añadido en v4, **RGB** (Chen, Lin, Han y Sun, 2024; arXiv:2309.01431). Cambios de
v4 (hoja `Cambios v4`):

- **RGB**: benchmark de capacidades del generador bajo RAG con documentos controlados (noise robustness, negative rejection,
  information integration, counterfactual robustness). Lo relevante aquí es *negative rejection*: la tasa con que el modelo se
  abstiene cuando ningún documento contiene la respuesta. No evalúa recuperador real, citas ni respuesta parcial. Referencia
  **pendiente de contrastar con el PDF** de los proceedings (las demás se verificaron en PDF).
- **RAGChecker** pasa a cubrir *parcialmente* el diagnóstico: ya atribuye por afirmación al recuperador (claim recall) o al
  generador (context utilization, hallucination, self-knowledge). Por eso la fila "Diagnóstico" y la RQ dejan de hablar de
  "origen de los errores".
- Fila nueva **Abstención**: RGB y FActScore (% de respuestas) son lo más cercano; ninguna liga la abstención con la cobertura
  del corpus por pregunta, con la abstención parcial ni con las citas.

### 7.2 Diferenciación de la contribución

Lo que ya existe y se reutiliza (y se cita): atribución por afirmación a recuperador o generador (RAGChecker); unidad de enunciado
y cita que sostiene / que no (ALCE); juzgar contra el contexto completo y no solo lo citado (CiteEval, que corresponde a distinguir
`SIN-CITA` de `CITA-X`); tasa de rechazo cuando los documentos no tienen la respuesta (RGB).

Lo que este protocolo añade, en una sola tabla por afirmación:

1. **Cobertura del corpus por pregunta como condición previa (N0).** Distingue "no estaba en el corpus" de "estaba y no llegó" y
   de "llegó y no se usó", y define cuándo la abstención es debida (parte no respondible) y cuándo es errónea (`ABS-E`, la
   evidencia llegó). RGB solo trata el caso extremo de ningún documento útil.
2. **Varios fallos por respuesta con referencia por hechos.** Una misma respuesta puede llevar E1 + E2 + E3 (p05) porque los
   hechos de la referencia se siguen uno a uno; las métricas por módulo de RAGChecker no separan "hecho omitido" de "hecho
   negado" ni de "correcto sin respaldo".
3. **Citas dentro de esa cadena.** `SOSTENIDA` / `CITA-X` / `SIN-CITA` / `SIN-RESPALDO` se juzgan por afirmación junto con
   `vs_ref`, lo que permite registrar "correcta pero sin respaldo" (p05) y citas en respuestas incorrectas.
4. **Condición de aplicación.** Ciberseguridad (MITRE ATT&CK), preguntas en español e inglés sobre evidencia en inglés, modelo
   local pequeño, protocolo manual con validación entre evaluadores.

### 7.3 Validación de consistencia (RQ6)

**Diseño.** Un segundo evaluador, independiente, calificó a ciegas (sin ver las notas del evaluador principal) las 4 preguntas
acordadas con el director: p01, p05, p06 y p09 (8 respuestas, 27 afirmaciones), en la plantilla vacía
`v2/calificacion_v2_eval_independent.xlsx`. Las afirmaciones ya estaban extraídas en la plantilla: el segundo evaluador juzgó
`tipo`, `vs_ref`, `hecho_ref` y `respaldo`, **no la extracción**. Es un límite declarado: el acuerdo mide la aplicación de la
rúbrica, no la descomposición en afirmaciones.

**Acuerdo bruto** (calificación del evaluador principal tras aplicar D2, frente a la del segundo evaluador tal como la entregó):

| Columna | Coincidencias | Kappa de Cohen |
|---|---|---|
| `vs_ref` | 22 / 27 (81 %) | 0,73 |
| `tipo` (hecho / abstención) | 26 / 27 (96 %) | 0,89 |
| `hecho_ref` (igualdad exacta) | 24 / 27 (89 %) | — |
| `respaldo` (5 pares comparables) | 4 / 5 | — |
| N2 por respuesta | 7 / 8 | — |
| Diagnóstico (lista de causas) | 7 / 8 | — |

**Desacuerdos y su causa.** Los 5 desacuerdos de `vs_ref` corresponden a dos reglas que v2.2 no hacía explícitas:

| Caso | Evaluador principal | Evaluador 2 | Regla que lo resuelve |
|---|---|---|---|
| p06 RAG #3, p09 RAG #3 (abstención sobre la parte no respondible) | `FUERA_REF` | `CORRECTA` | D2: no enuncia ningún hecho → `FUERA_REF`; se registra como abstención debida en la lectura B |
| p06 LLM #2, p09 LLM #5 (hecho sobre la parte no respondible) | `FUERA_REF` + `NO-ABS` | `CORRECTA` | D2 y regla de parte no respondible |
| p01 LLM #5 (cubre H3 de forma indirecta) | `FUERA_REF` | `CORRECTA` (H3) | D2: no enuncia el hecho |

Los demás desacuerdos: p06 LLM #1 ("ATT&CK no documenta…"), `hecho` frente a `abstencion` → regla abstención vs. afirmación de
ausencia (§3.2), sin efecto en el diagnóstico (ambos van a E2 y `CRITICA`); p09 RAG #2 (SPF/DKIM/DMARC), `CORRECTA`/H5 frente a
sin `hecho_ref` → regla de enunciación: sí enuncia M1054, y la negación de la misma respuesta se registra como `ABS-E` (D3), lo que
explica la única diferencia de N2 (1 frente a 0); p05 RAG #2, `SOSTENIDA` frente a `CITA-X` → el fragmento expresa la relación
textualmente (§4.2).

**Acuerdo tras aplicar las reglas congeladas a ambas calificaciones:** `vs_ref` 26 / 27 (96 %), kappa 0,94. El caso restante es
p09 RAG #2 (asignación de `hecho_ref`). Se reporta el acuerdo bruto como medida de consistencia de v2.2 y el acuerdo tras las
reglas como evidencia de que los desacuerdos eran de regla, no de lectura; v2.3 incorpora esas reglas con sus ejemplos.

**Límites.** 4 preguntas y 27 afirmaciones: el kappa es descriptivo, no una estimación poblacional. Un solo evaluador adicional.
Afirmaciones pre-extraídas. La validación de la extracción de afirmaciones y de la tabla de hechos queda para la corrida nueva, si
hay tiempo (§8).

**Juez LLM, solo contraste.** Antes de la calificación manual, Claude (sesión de 2026-10-12, recreada el 2026-10-20) calificó las
mismas 8 respuestas con la rúbrica v2 y sin ver notas humanas (`ejemplos_calificados_v2.md`). Coincidió con el evaluador principal
en N2 en 7 de 8 y en el diagnóstico en 7 de 8; las diferencias (p06 LLM #2 y p09 RAG #3, parte no respondible; p09 LLM #5) son
los mismos casos de la regla D2. No se usa como validación (D7). Lo que falta documentar de ese contraste: modelo exacto e
instrucciones completas no se guardaron en el archivo; se anota como límite y no se repite salvo que se registre todo.

## 8. Corrida reproducible

Requisitos (fijados en v2.2 §8, decisiones D1 y D6) y estado:

| # | Requisito | Estado 2026-10-30 |
|---|---|---|
| 1 | Corregir el solape duplicado del chunking (`app/rag/chunking.py`) y reingerir | **código hecho y probado** (`eval/pilot/tests/test_chunking.py`: reproduce el defecto con el código viejo y pasa con el nuevo, incluidos G0032, G0016, M1038, S0154, T1110.003). Causa: `_hard_split` ya solapaba y `split_text` anteponía otra vez la cola de 150. Corpus completo: 7.241 → 7.244 chunks, ninguno > 1.200. **Reingesta pendiente** (`FORCE_REINGEST=true`, ~60 min CPU); los `point_id` de documentos largos cambian |
| 2 | Comprobar que la ingesta esté completa | **hecho**: `ingest.py` falla si `points_count ≠ len(records)`; `eval/pilot/check_ingest.py` compara `chunks.jsonl`, manifest y Qdrant (`/health`) y `run_pilot.py` lo invoca antes de cada corrida |
| 3 | Proteger las calificaciones | **hecho**: `run_pilot.py` (corrida y `--rebuild-xlsx`) se niega a sobrescribir `calificacion.xlsx` sin `--force`; verificado contra el piloto |
| 4 | `--resume` se niega si cambia la configuración | **hecho**: compara model, embed_model, retrieval, top_k, temperature, think, modes, num_ctx, num_predict y hash del corpus; el `config.json` del piloto (sin esos campos) no es reanudable con la versión nueva, por diseño |
| 5 | Manifest del corpus, textos gold y límites de generación por corrida | **hecho**: `config.json` guarda `num_ctx`, `num_predict` y `corpus` (versiones ATT&CK, fecha de ingesta, n_chunks, chunk_size/overlap, sha256 de `chunks.jsonl`); cada corrida escribe `questions_snapshot.jsonl` y `gold_chunks.jsonl` |
| 6 | Desempate determinista en la recuperación (D6) | **código hecho**: `vectorstore.rank_hits` ordena por (score, `point_id`) sobre `top_k × 4` candidatos; probado con el empate de p01. **No verificado contra Qdrant en marcha**; confirmar con `--check-ties` en la corrida nueva |
| 7 | Piloto original intacto | se mantiene (verificado con `git status`) |

Pruebas: `eval/pilot/tests/` (3 archivos, 10 pruebas; se ejecutan con `python <archivo>`, no hay pytest). Nada se probó contra
Qdrant/Ollama/API en marcha. La API monta `./app` con `--reload`, así que los cambios aplican sin rebuild; la ingesta sí requiere
reingerir.

**Conjunto nuevo de preguntas.** Se propone tras cerrar este documento: equilibrado por cobertura del corpus (completa / parcial /
nula), con `reference` y hechos `H#` verificados en `chunks.jsonl` **tras la reingesta** (los `point_id` cambian), tamaño
dimensionado por el tiempo disponible para calificar (la calificación es manual por diseño). Misma configuración que el piloto
(`top_k=5`, mismo modelo) para que la rúbrica, no el sistema, sea lo que cambia.

**Qué se reporta de la corrida nueva:** las lecturas A–D (§5), N1 por evidencia, la tabla de diagnósticos y la comparación con el
piloto como dos corridas de la misma rúbrica sobre conjuntos distintos (no como una mejora del sistema).

## 9. Propuesta de evaluación final

Se redacta después de la corrida (§8), con el director. Contenido previsto: alcance (protocolo diagnóstico aplicado a dos corridas),
RQ1–RQ6 con la evidencia que las responde, limitaciones (§6, §7.3) y trabajo futuro (§10).

## 10. Trabajo futuro (fuera del alcance por decisión D8)

- **Módulo de evaluación y auditoría continua**: `grade()` como función pura y versionada sobre las tablas `Afirmaciones` +
  `Hechos`, política de alertas configurable por despliegue, CLI/API. La separación medición / alerta de §3.6 lo deja preparado.
- Extracción de afirmaciones asistida por un LLM distinto del generador, con revisión humana (los juicios `vs_ref` y `respaldo`
  siguen siendo manuales).
- Validación de la extracción de afirmaciones y de la tabla de hechos con un segundo evaluador.
- Efecto del idioma con preguntas equivalentes en ambos idiomas.

## 11. Casos ambiguos y su resolución (v1.1 → v2.3)

| Caso | Pregunta(s) | v1.1 | v2.3 |
|---|---|---|---|
| Gold parcial: N1 = SI pero falta un gold | p02, p09 | E1 o E2 según dónde estaba lo omitido | N1 por evidencia y `llegó` por hecho (§4.1) |
| Evidencia alternativa en fragmentos no gold | p05 | Anotar | `alt` / `alt-parcial`; `ALT-P` no cuenta (D1) |
| Correcto sin soporte en el contexto | p05 | N3 baja | `CORRECTA` + `SIN-RESPALDO` (§3.2) |
| LLM correcto fuera de la referencia | p10, p11, precio de p04 | Anotar | `FUERA_REF` / `NO-ABS`, reportado aparte |
| Afirmación que cubre un hecho de forma indirecta | p01 LLM | — | `FUERA_REF` (D2) |
| Abstención sobre la parte no respondible | p06, p09 | — | `FUERA_REF` sin código; abstención debida en lectura B (D2) |
| Hecho que llegó, se cubre y a la vez se niega | p06 RAG, p09 RAG | N2 = 0 | cobertura cuenta; `ABS-E` + E2 + `CRITICA` (D3, D4) |
| Afirmación de ausencia sobre la fuente | p06 LLM, p09 LLM | — | `hecho` `INCORRECTA` → `INC` (§3.2) |
| N3 ante abstención | p08, p10–p13 | N/A | N/A; abstenciones no se califican en citas |
| Respuesta truncada | p01 LLM | Anotar | `TRUNC` (§3.3, §3.6) |

## 12. Entregables y estado

| # | Entregable | Estado |
|---|---|---|
| 1 | RQ y sub-preguntas (§1) | v2.3 |
| 2 | Matriz comparativa (ALCE, CiteEval, RGB) | hecha: `matriz_comparativa_evaluacion_RAG_v4.xlsx` (RGB pendiente de PDF) |
| 3 | Piloto: preguntas, trazas, calificación completa por afirmación | hecho (`v2/calificacion_v2.xlsx`, 26 respuestas) |
| 4 | Rúbrica congelada | este documento |
| 5 | Plantilla Excel y scripts de apoyo | hechos (`v2/`, `*.py`) |
| 6 | Validación de consistencia (§7.3) | hecha (4 preguntas, segundo evaluador) |
| 7 | Corrida reproducible y conjunto nuevo de preguntas (§8) | en curso |
| 8 | Propuesta de evaluación final (§9) | pendiente, tras §8 |

---

## Anexo A. Rúbrica v1.1 original (para comparabilidad del piloto)

Una fila por pregunta × modo (`results/20260922_064359/calificacion.xlsx`).

| Nivel | Valores | Regla |
|---|---|---|
| N0 corpus (auto) | completa / parcial / nula | Viene del diseño de la pregunta |
| N1 recuperación (auto, solo RAG) | SI / NO + rango | Algún fragmento gold entre los top-k |
| N2 respuesta (manual) | 2 / 1 / 0 | 2 correcta y completa · 1 a medias · 0 incorrecta o inventada. Nula: 2 = se abstuvo, 0 = inventó |
| N3 citas (manual, solo RAG) | 2 / 1 / 0 / N/A | 2 toda afirmación citada y sostenida · 1 alguna sin cita o cita que no la sostiene · 0 sin citas o equivocadas · N/A si se abstuvo |
| Diagnóstico (manual) | OK / E0 / E1 / E2 / E3 | Primer eslabón que falló |

Resultado v1.1 (13 × 2): N2 promedio RAG 1,23 / LLM 0,54; N3 RAG 1,71; hit@5 6/9. Esta lectura queda sustituida por §5.3.

## Anexo B. Correspondencia v1.1 → v2.3

| v1.1 | v2.3 |
|---|---|
| N2 manual 0/1/2 | derivado de `Afirmaciones` + `Hechos` (§3.4); misma escala |
| N3 manual 0/1/2/N/A | derivado (§3.4); `SIN-R` y `CITA-X` se distinguen |
| "correcto sin soporte" (p05) | `vs_ref=CORRECTA` + `respaldo=SIN-RESPALDO` |
| abstención errónea (p09) | `tipo=abstencion` + `vs_ref=INCORRECTA` → `ABS-E` |
| E0-corpus en modo LLM | `E0-no-abstencion` |
| primer eslabón | lista de causas; el primer eslabón se deriva solo para comparar |
| "correcto fuera de la referencia" | `FUERA_REF`, reportado aparte |
| N1 = algún gold | N1 por evidencia (NINGUNA/PARTE/TODA) |

## Anexo C. Archivos del proyecto (`RAG/eval/pilot/` salvo indicación)

| Archivo | Contenido |
|---|---|
| `protocol.md`, `protocol_v2.md`, `protocol_v2.2.md` | Versiones anteriores (intactas) |
| `protocol_v2.3.md` | Este documento (rúbrica congelada) |
| `questions.jsonl`, `results/20260922_064359/` | Preguntas y corrida del piloto (intactos) |
| `v2/calificacion_v2.xlsx` | Calificación completa del piloto por afirmación (evaluador principal, 2026-10-22 / 30) |
| `v2/calificacion_v2_eval_independent.xlsx` | Segundo evaluador (p01, p05, p06, p09) |
| `borrador_ejemplos_reunion.md` | Cuatro casos calificados por afirmación, con los puntos discutidos |
| `ejemplos_calificados_v2.md`, `afirmaciones_ejemplos.csv` | Contraste con juez LLM (exploratorio) |
| `evidence_build.py`, `evidence_pilot.json`, `evidence_check.py` | Tabla de evidencia y cálculo de N1 |
| `comparar_modos.py`, `build_calificacion_v2.py`, `v2/*.xlsx` | Cálculo de lecturas y plantilla Excel |
| `../../../matriz_comparativa_evaluacion_RAG_v4.xlsx` | Matriz con ALCE, CiteEval y RGB (carpeta `CAPSTON`) |
