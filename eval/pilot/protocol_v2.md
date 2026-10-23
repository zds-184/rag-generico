# Evaluación diagnóstica del RAG — protocolo v2 (borrador)

Deriva de `protocol.md` (v1.1), que queda intacto junto con la corrida `20260922_064359`.
Estado: **§3 (qué se califica), §4 (recuperación y citas) y §5 (comparación con y sin RAG) están redactados**. Los demás puntos se añaden uno a uno tras revisión.

| § | Tema | Estado |
|---|---|---|
| 3 | Qué se califica (afirmaciones, códigos, derivación) | borrador |
| 4 | Recuperación (N1) y citas | borrador |
| 5 | Comparación con y sin RAG | borrador |
| 6 | Validación (2.º evaluador) y matriz (ALCE, CiteEval) | pendiente |
| 7 | Corrida reproducible | pendiente |

## 3. Qué se califica

Una respuesta se descompone en **afirmaciones atómicas** (máx. ≈6; si hay más, las que sustentan la referencia).
Cada afirmación se juzga en **dos ejes independientes**:

- **Corrección** frente a la `reference` (la misma para ambos modos). La cobertura del corpus (N0) es la condición de
  referencia: que algo no esté en el corpus no lo hace falso.
- **Respaldo** frente a los fragmentos que el sistema recibió (solo modo RAG).

Una respuesta puede tener varios problemas a la vez; no se elige solo el primero.

### 3.1 Hoja `Hechos` (una vez por pregunta)

La referencia se descompone en hechos atómicos `H1..Hn` (n = 0 en preguntas nulas). Para la parte no respondible se
registra `unanswerable_part`. En modo RAG se añade por corrida la columna `llegó` (SI / ALT / ALT-P / NO), calculada
automáticamente como se describe en §4.1. Es la base de omisiones y de E1 vs E2.

### 3.2 Hoja `Afirmaciones` (una fila por afirmación × modo)

| Columna | Valores |
|---|---|
| `tipo` | `hecho` (afirma algo) · `abstencion` (dice que no hay información / no puede responder) |
| `vs_ref` | `CORRECTA` · `INCORRECTA` · `FUERA_REF` (ni confirma ni contradice la referencia) |
| `hecho_ref` | `H#` que cubre, si aplica |
| `respaldo` (solo RAG, solo `hecho`) | `SOSTENIDA` (con cita [n] cuyo fragmento la sostiene) · `CITA-X` (cita, pero ese fragmento no la sostiene) · `SIN-CITA` (sin cita, pero algún fragmento recibido la sostiene) · `SIN-RESPALDO` (ningún fragmento recibido la sostiene, tenga cita o no) |
| `cita_n`, `fragmento_sostiene` | rango [n] citado; rango del fragmento que realmente la sostiene (o vacío) |
| `nota` | texto libre |

Aclaraciones surgidas al calificar los ejemplos (`ejemplos_calificados_v2.md`):
- **Abstención vs. afirmación de ausencia.** `abstencion` = el modelo dice que *el contexto/él no tiene* la información
  ("los pasajes no dicen…"). Una afirmación sobre la fuente ("ATT&CK no documenta…", "no hay mitigaciones") es un `hecho`
  y puede ser `INCORRECTA`.
- **Listas cerradas.** Elementos extra que la referencia no incluye son `FUERA_REF` (se reportan aparte como extras), no
  `INCORRECTA`; solo se marca `INCORRECTA` lo que contradice la referencia. En modo RAG un extra además recibe `respaldo`.
- **`llegó`** se determina leyendo los fragmentos recibidos (no solo `gold_points_found`), para registrar evidencia alternativa.

Fuera de la tabla: filas `OMISION` por cada `H#` de la referencia que ninguna afirmación `CORRECTA` cubre, y el
indicador `TRUNC` por respuesta si `completion_tokens` = límite (`LLM_NUM_PREDICT`).

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

Se aplican aunque la respuesta sea incorrecta: una afirmación incorrecta también se revisa en citas.
Una abstención correcta (`tipo=abstencion`, `vs_ref=CORRECTA`, sobre la parte no respondible) no genera código.
`FUERA_REF` que no responde a la parte no respondible (dato extra, cierto o no) se reporta aparte como "fuera de la
referencia"; no cuenta como error.

### 3.4 Notas derivadas (resumen, reemplazan el 0/1/2 manual)

Sea H = nº de hechos de la referencia y C = nº de hechos cubiertos por afirmaciones `CORRECTA`.

**N2 (correcta y completa).**
- Si H = 0 (pregunta nula): **2** si no hay `NO-ABS`, **0** si lo hay.
- Si H > 0: **2** si C = H y no hay `INC`, `ABS-E` ni `NO-ABS`; **0** si C = 0; **1** en los demás casos.

**N3 (citas, solo RAG).** Se calcula sobre las afirmaciones `hecho`.
- **N/A** si no hay ninguna (abstención total).
- **2** si todas son `SOSTENIDA`; **0** si ninguna lo es; **1** en los demás casos.

**Sin topes (decisión 2026-10-12).** N2 y N3 son descriptivos y monótonos: no hay reglas del tipo "si hay X entonces N2 = 0".
Los problemas graves no se esconden en la nota; se señalan con las alertas de §3.7. Por eso p06 (RAG) y p09 (LLM) dan
N2 = 1 aunque el piloto les puso 0: el piloto mezclaba cobertura y veredicto final en un solo número.

### 3.5 Diagnóstico: lista de causas (reemplaza "primer eslabón")

| Etiqueta | Se asigna cuando |
|---|---|
| `E0-no-abstencion` | hay `NO-ABS` (se renombra desde "E0-corpus"; mismo significado en ambos modos) |
| `E1-recuperacion` | hay `OMI`, `INC` o `ABS-E` sobre un hecho con `llegó = NO` |
| `E2-generacion` | hay `OMI`, `INC` o `ABS-E` sobre un hecho con `llegó = SI/ALT` |
| `E3-citas` | hay `CITA-X`, `SIN-C` o `SIN-R` |
| `OK` | ninguna de las anteriores |

- Una respuesta lleva todas las etiquetas que apliquen (p. ej. `E2 + E3`). La columna "primer eslabón" se deriva con el
  orden E0 → E1 → E2 → E3 para poder comparar con el piloto.
- **Modo LLM**: no hay recuperación ni fragmentos; `llegó` y `respaldo` no aplican, así que solo pueden aparecer
  `E0-no-abstencion` y `E2-generacion` (aquí "no lo sabía o lo recordó mal"). `SIN-R` no se genera.
- `TRUNC` se reporta como indicador aparte, no como causa E.

### 3.7 Alertas derivadas (política, separada de la medición)

La **medición** (afirmaciones → códigos, cobertura, N2, N3) es fija y lleva la versión de la rúbrica. La **política** decide
qué merece atención y es configurable sin tocar la medición. Política por defecto:

| Alerta | Se activa cuando la respuesta tiene |
|---|---|
| `CRITICA` | `ABS-E`, `NO-ABS` o `INC` |
| `RESPALDO` | `SIN-R` o `CITA-X` (y `SIN-C`, como aviso menor) |
| `TRUNC` | respuesta truncada |

Una respuesta puede tener varias. Las alertas no cambian N2 ni N3; se reportan junto a ellos (columna `alertas`).

### 3.6 Correspondencia con v1.1

| v1.1 | v2 |
|---|---|
| N2 manual 0/1/2 | derivado de `Afirmaciones` + `Hechos` (§3.4); misma escala |
| N3 manual 0/1/2/N/A | derivado (§3.4); `SIN-R` y `CITA-X` se distinguen |
| "correcto sin soporte" (p05) | `vs_ref=CORRECTA` + `respaldo=SIN-RESPALDO` |
| abstención errónea (p09) | `tipo=abstencion` + `vs_ref=INCORRECTA` → `ABS-E` |
| E0-corpus en modo LLM | `E0-no-abstencion` |
| primer eslabón | derivado de la lista |
| "correcto fuera de la referencia" | `FUERA_REF`, reportado aparte |

## 4. Recuperación (N1) y citas

### 4.1 N1 por evidencia, no por fragmento gold

El piloto medía N1 como "llegó algún `gold_point_id`". Eso ignora (a) que haya llegado solo una parte de lo necesario y
(b) que el mismo hecho esté en fragmentos no gold. En v2 N1 se calcula **por hecho**:

1. Cada hecho `H#` de la referencia tiene una lista de **fragmentos de evidencia** del corpus (`evidence_pilot.json`,
   generada con `evidence_build.py` por búsqueda de ID de ATT&CK y texto en `chunks.jsonl`; el evaluador verifica las
   entradas `alt` y `alt-parcial`). Cada fragmento es de tipo:
   - `gold`: está en `gold_point_ids` de la pregunta;
   - `alt`: no es gold pero sostiene el hecho por sí solo (p. ej. el documento del software en lugar del del grupo);
   - `alt-parcial`: lo sostiene de forma indirecta o genérica (p. ej. la mitigación del padre T1059 para una sub-técnica,
     o el software que "usa" una técnica para decir que el grupo la usa).
2. `llegó` por hecho y respuesta RAG (`evidence_check.py`, automático): **SI** si llegó un fragmento gold; **ALT** si solo
   llegó una alternativa; **ALT-P** si solo llegó una parcial; **NO** si ninguno.
3. **N1 de la pregunta**: **NINGUNA** (ningún hecho con SI/ALT), **PARTE** o **TODA**, junto con la fracción
   *hechos que llegaron ÷ hechos totales* y el rango del mejor fragmento de evidencia. En preguntas nulas N1 = N/A.
4. **ALT-P no cuenta como "llegó"** por defecto (criterio estricto); se lista aparte (`hechos_llegaron_incl_alt_parcial`)
   y el evaluador puede aceptarla justificándolo en `nota`; entonces el hecho se trata como ALT para E1 vs E2.
5. `hit@k` y `recall@k` por gold se conservan como columnas secundarias para comparar con el piloto. **No son el veredicto**:
   un hit gold no implica suficiencia (p09: hit = SI pero llegaron 2 de 6 hechos) y un fallo gold no implica que no
   llegara evidencia (p05: gold 0/3, pero H2 y H3 llegaron como ALT).
6. N1 alimenta el diagnóstico: un hecho omitido, incorrecto o negado con `llegó = NO` → E1; con `SI`/`ALT` → E2 (§3.5).

### 4.2 Citas: reglas de decisión (por afirmación de `hecho`, solo modo RAG)

- **Soporte = el fragmento expresa la relación**, no solo nombra las entidades. Dos nombres en la misma lista no sostienen
  "A usa B" (p05, afirmación "APT29 usa Mimikatz" → `SIN-RESPALDO`).
- **Alcance de la cita.** Una cita [n] cubre las afirmaciones de su misma frase o viñeta. La repetición en una "respuesta
  final" cuenta como la misma cita, no como otra.
- **Cabecera cortada por el chunking.** Si el contenido sostiene la afirmación aunque falte la etiqueta (M1054 en p09),
  cuenta como sostenida.
- **Se revisan siempre**, también en respuestas incorrectas: una afirmación incorrecta con cita se califica igual que una
  correcta (`SOSTENIDA`, `CITA-X`, `SIN-CITA`, `SIN-RESPALDO`).
- **Las abstenciones no se califican en citas.** Si el hecho sí llegó, es un problema de generación (`ABS-E` → E2). La
  cita que acompañe a una abstención se anota en `nota` pero no entra en N3 ni en las métricas siguientes.
- **`SIN-CITA` no cuenta como respaldada** en N3 (conserva el criterio de v1.1), pero se reporta aparte para no
  confundirla con una afirmación sin base.

### 4.3 Métricas de recuperación y citas (hoja `Resumen`)

| Métrica | Definición | Nivel |
|---|---|---|
| N1 por pregunta | NINGUNA / PARTE / TODA + hechos llegados ÷ hechos totales | pregunta |
| Cobertura de recuperación | Σ hechos llegados ÷ Σ hechos (respondibles) | agregado |
| Precisión de citas | afirmaciones de hecho `SOSTENIDA` ÷ afirmaciones de hecho (= base de N3) | respuesta / agregado |
| Cobertura de citas | hechos de la referencia cubiertos por una afirmación `CORRECTA` y `SOSTENIDA` ÷ hechos totales | respuesta / agregado |
| `SIN-RESPALDO`, `CITA-X`, `SIN-CITA` | conteo de cada uno, por separado | agregado |

La cobertura de citas es la métrica comparable con las de evaluación de citas de ALCE (precisión/recall de citas); su
comparación formal con ALCE y CiteEval se hace en §6.

### 4.4 Archivos de apoyo (piloto)

| Archivo | Contenido | Modifica el piloto |
|---|---|---|
| `evidence_build.py` → `evidence_pilot.json` | hechos y fragmentos de evidencia por pregunta | no (solo lee `chunks.jsonl` y `questions.jsonl`) |
| `evidence_check.py <corrida>` → `<corrida>/n1_v2.json` | `llegó` por hecho y N1 de cada respuesta RAG | solo agrega un archivo nuevo; no toca `traces.jsonl` ni `calificacion.xlsx` |

## 5. Comparación con y sin RAG

### 5.1 Qué se compara y qué no

Ambos modos usan el mismo modelo y configuración (§2 de v1.1). La vara es la misma `reference`, que es **cerrada al
corpus** (ATT&CK Enterprise ingestado). Por eso la comparación mide fidelidad a esa referencia y abstención; **no** mide
veracidad general. Una afirmación cierta en el mundo pero ausente de la referencia es `FUERA_REF` (§3.3): se cuenta y se
reporta, no se premia ni se penaliza, y no se verifica contra fuentes externas.

La diferencia de N2 entre modos **deja de ser el titular** de la comparación (mezclaba fidelidad, abstención y respaldo,
y penalizaba al LLM por construcción). N2/N3 se conservan como resumen descriptivo. El titular son cuatro lecturas
separadas, todas derivadas de `Afirmaciones` y `Hechos` sin calificación adicional:

| Lectura | Métrica | Modos | Pregunta que responde |
|---|---|---|---|
| **A. Fidelidad a la referencia** | cobertura de hechos (C ÷ H) y proporción de afirmaciones `INCORRECTA` (÷ afirmaciones de hecho) | ambos | ¿Dijo lo que ATT&CK dice y cuánto contradijo? |
| **B. Abstención** | estado en la parte respondible y en la no respondible (5.2) | ambos | ¿Se abstuvo cuando debía y cuando no debía? |
| **C. Respaldo documental** | precisión y cobertura de citas, `SIN-RESPALDO`/`CITA-X`/`SIN-CITA` (§4.3) | solo RAG | ¿Lo dicho está sostenido por lo recibido? |
| **D. Fuera de referencia** | conteo de afirmaciones `FUERA_REF` | ambos | ¿Qué más dijo? (sin juicio de valor) |

C no es una comparación: el LLM no recibe fragmentos, así que su respaldo documental es N/A por construcción y no se
reporta como falla.

### 5.2 Lectura B: estados de abstención

Por respuesta, en la **parte respondible** (H > 0): `responde` (C = H, sin `ABS-E`) · `responde parcial` · `responde parcial + ABS-E`
· `se abstiene (ABS-E)` (C = 0 y niega lo que la referencia contiene) · `no cubre` (C = 0 sin abstenerse). En la **parte
no respondible** (`unanswerable_part` o pregunta nula): `se abstiene` · `responde (NO-ABS)` · `no la aborda`.
Se reporta el conteo de cada estado por modo. Las dos tasas de interés son: abstención errónea (`ABS-E` en partes
respondibles) y respuesta sin base (`NO-ABS` en partes no respondibles).

### 5.3 Reporte

- Una **tabla emparejada por pregunta** (misma pregunta, ambos modos) con cobertura, `INCORRECTA`, estado de abstención,
  `FUERA_REF`, N2 y N3, más **totales descriptivos** por modo (hechos cubiertos ÷ hechos de las preguntas incluidas).
- **Sin pruebas de significancia**: con tan pocas preguntas no las sostendrían; se reportan conteos y se señalan los casos
  concretos que explican cada diferencia.
- Se permite concluir, p. ej., "frente a la referencia, el RAG cubre X de Y hechos y se abstiene en N de M partes sin
  respuesta". No se permite concluir "el RAG es más veraz que el LLM".
- Lectura del piloto "el RAG duplica el N2 del mismo LLM": se sustituye por A–D. Con los 8 casos ya calificados por
  afirmación (`afirmaciones_ejemplos.csv`) la cobertura total es 4/18 en ambos modos, pero distribuida distinto (p05 y p06
  favorecen al RAG; p01 y p09 al LLM, este último con `INCORRECTA` y `NO-ABS`): una sola nota esconde esa estructura.

### 5.4 Cálculo

`comparar_modos.py [afirmaciones.csv]` lee un CSV con las columnas `qid, modo, n, afirmacion, tipo, vs_ref, hecho_ref,
zona, respaldo, cita_n, fragmento_sostiene, nota` (`hecho_ref` admite varios `H#` separados por `;`; `zona` = `ref` o
`no_resp`; `respaldo` vacío en modo LLM), cruza con `evidence_pilot.json` y `questions.jsonl`, y deriva N2, N3 (§3.4) y
las lecturas A–D. No escribe archivos. `afirmaciones_ejemplos.csv` contiene las 8 respuestas calificadas en
`ejemplos_calificados_v2.md` y sirve de plantilla y de prueba del cálculo (reproduce sus N2/N3).

### 5.5 Plantilla de calificación (Excel)

`build_calificacion_v2.py <corrida>` genera `eval/pilot/v2/calificacion_v2_piloto.xlsx` a partir de una corrida (solo lee) y
**se niega a sobrescribir** un libro existente. Hojas: `Guia`, `Respuestas` (una fila por pregunta × modo; todo lo derivado
en verde), `Afirmaciones` (donde se califica a mano, con listas desplegables y una columna de chequeo), `Hechos` (referencia
descompuesta y `llegó`), `Contextos`, `Resumen` (lecturas A-D y alertas) y `Config` (corrida, corpus, evaluador). Con `--demo`
genera `calificacion_v2_DEMO.xlsx`, relleno con las 27 afirmaciones de los ejemplos y una columna "esperado"; sirve de prueba
de las fórmulas (verificadas con un motor independiente; pendiente abrirlas en Excel).
