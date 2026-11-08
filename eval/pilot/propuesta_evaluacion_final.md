# Propuesta de evaluación final — borrador para el director

**Estudiante:** Darwin Simba · **Fecha:** 2026-11-08 · **Estado:** borrador v0.1 para revisión (§9 del protocolo v2.3)
**Repositorio:** https://github.com/zds-184/rag-generico · **Documentos base:** `eval/pilot/protocol_v2.3.md` (rúbrica congelada),
`matriz_comparativa_evaluacion_RAG_v4.xlsx` (posicionamiento), `eval/pilot/v2/calificacion_v2.xlsx` (piloto) y
`eval/run2/calificacion_v2_run2.xlsx` (corrida 2).

Profesor, le presento cómo propongo cerrar la evaluación del proyecto. Sigo el orden que acordamos el 29 de octubre: rúbrica
congelada, corrida reproducible y, ahora, la propuesta final. Marco con **[decisión]** los puntos en los que necesito su criterio.

## 1. Qué se evalúa y qué se entrega

La contribución del proyecto no es el sistema RAG (es un RAG genérico local sobre MITRE ATT&CK Enterprise v19.2, construido como
banco de pruebas) sino el **protocolo de evaluación diagnóstica manual por afirmación**, que para cada pregunta registra:

1. **N0 – corpus**: si la información necesaria existía en el corpus (completa, parcial o nula), con una referencia cerrada al
   corpus descompuesta en hechos H1…Hn y verificada contra `documents.jsonl`.
2. **N1 – recuperación**: si cada hecho llegó al contexto (gold, evidencia alternativa, parcial o nada).
3. **N2 – generación**: cada afirmación de la respuesta frente a la referencia (`CORRECTA` / `INCORRECTA` / `FUERA_REF`),
   separando hechos de abstenciones y la parte respondible de la no respondible.
4. **N3 – citas**: si cada afirmación de hecho está sostenida por el fragmento que cita.

De esa tabla única se derivan los códigos (INC, OMI, ABS-E, NO-ABS, SIN-R, CITA-X, SIN-C), las notas N2/N3, las cuatro lecturas
comparativas A–D entre el mismo modelo con y sin recuperación, y un diagnóstico por respuesta que admite varios fallos a la vez
(E0 corpus, E1 recuperación, E2 generación, E3 citas). La política de alertas (CRITICA, RESPALDO, TRUNC) queda separada de la
medición y solo se reporta.

**Entregables finales propuestos:**

| # | Entregable | Estado |
|---|---|---|
| 1 | Protocolo v2.3 (rúbrica congelada, decisiones D1–D8, casos ambiguos, anexos) | hecho |
| 2 | Matriz comparativa v4 (RAGAS, RAGChecker, ARES, FActScore, RefChecker, ALCE, CiteEval, RGB), 8 referencias verificadas contra PDF | hecha |
| 3 | Piloto: 13 preguntas, 26 respuestas calificadas, trazas completas, corpus congelado | hecho |
| 4 | Corrida 2 reproducible: código corregido y probado, corpus reingestado con manifest, 18 preguntas 6/6/6, 36 respuestas calificadas, réplicas documentadas | hecha |
| 5 | Validación de consistencia con segundo evaluador (RQ6) | hecha |
| 6 | Esta propuesta → capítulo de evaluación del documento final | borrador |
| 7 | Documento de tesis y defensa | pendiente **[decisión: estructura y fechas]** |

## 2. Cómo responde la evidencia a cada sub-pregunta

| | Sub-pregunta | Evidencia disponible | Respuesta propuesta |
|---|---|---|---|
| RQ1 | ¿Existía la información en el corpus? | 31 preguntas en dos conjuntos (completas 11, parciales 10, nulas 10), cada referencia verificada literalmente en el corpus; categorías nuevas en la corrida 2: técnica retirada (n15) y conocimiento MITRE adyacente (n18) | Sí: N0 se fija por diseño y queda registrado por pregunta, cosa que ninguna de las ocho métricas de la matriz hace |
| RQ2 | ¿La recuperación trajo la evidencia? | `llegó` por hecho leído en los contextos; gold en el top-5 en 6/9 (piloto) y 10/12 (corrida 2) preguntas respondibles; desempate determinista verificado en vivo (D6) | Sí, por hecho y aceptando evidencia alternativa; los fallos de recuperación se localizan (p01, p08; n02, n03, n07, n12) |
| RQ3 | ¿Cada afirmación es correcta, completa y fiel? | 234 afirmaciones calificadas (92 piloto + 142 corrida 2) | Sí; la regla de enunciación (D2) es la que más decisiones resuelve |
| RQ4 | ¿Cada afirmación está sostenida por su cita? | precisión de citas 71 % (piloto) y 74 % (corrida 2); cobertura de citas 39 % → 55 %; códigos CITA-X / SIN-CITA | Sí; el defecto dominante cambia de CITA-X (piloto) a SIN-CITA (corrida 2: listas sin [n]), mismo problema de generación |
| RQ5 | ¿En qué se diferencian con y sin recuperación? | Lecturas A–D en ambas corridas (tabla §3) | El RAG cubre más hechos (42 % y 64 % frente a 21 % y 17 %), nunca responde sin base (NO-ABS 0 frente a 7 y 8) y su coste es la abstención errónea cuando la evidencia no llega (ABS-E 3 y 4, casi siempre con `llegó = NO`) |
| RQ6 | ¿Es consistente entre evaluadores? | Segundo evaluador independiente en 4 preguntas / 27 afirmaciones: `vs_ref` 22/27 (κ 0,73) en bruto y 26/27 (κ 0,94) tras aplicar las reglas congeladas; `tipo` 26/27 | Sí en lo esencial; 4 de los 7 desacuerdos brutos eran una sola regla (parte no respondible), que D2 cerró. Límite: afirmaciones pre-extraídas, muestra pequeña, un evaluador adicional |

## 3. Resultados que propongo reportar (descriptivos, sin pruebas de significancia)

| Lectura | Piloto RAG | Piloto LLM | Corrida 2 RAG | Corrida 2 LLM |
|---|---|---|---|---|
| A. Hechos cubiertos | 14/33 (42 %) | 7/33 (21 %) | 27/42 (64 %) | 7/42 (17 %) |
| A. Afirmaciones INCORRECTA | 19 % | 23 % | 0 % (0/38) | 27 % (22/82) |
| B. Respuestas con ABS-E | 3 | 1 | 4 | 0 |
| B. Respuestas con NO-ABS | 0 | 7 | 0 | 8 |
| C. Precisión / cobertura de citas | 71 % / 39 % | — | 74 % / 55 % | — |
| C. SIN-R / CITA-X / SIN-C | 1 / 4 / 1 | — | 0 / 1 / 9 | — |
| D. Afirmaciones FUERA_REF | 3 | 33 | 10 | 52 |
| N2 promedio | 1,38 | 0,38 | 1,61 | 0,17 |
| Diagnóstico dominante | E1 y E1+E3 | E2 | OK (9) y E3 (5) | E2 (10) y E0 (6) |

Las dos corridas se presentan como **dos aplicaciones de la misma rúbrica sobre conjuntos distintos**, no como una mejora del
sistema: la diferencia en INCORRECTA del RAG (19 % → 0 %) se explica porque el conjunto 2 tiene menos preguntas de relación entre
objetos (tipo p05), y la del defecto de citas (CITA-X → SIN-CITA) porque cambió el tipo de lista pedida. Lo que se mantiene en
ambas es lo que propongo como hallazgo: (a) el RAG no responde sin base y el LLM lo hace en todas las nulas; (b) cuando el RAG
falla, el protocolo localiza si fue la recuperación (E1, la mayoría) o la generación (E2, un caso por corrida); (c) las citas
fallan por forma (sin [n]) más que por fondo (SIN-RESPALDO 1 y 0).

**[decisión]** ¿Le parece suficiente reportar las dos corridas así, o quiere una tercera con otro conjunto / otro `top_k` para
reforzar la lectura de recuperación? Mi propuesta es no añadir corridas: el objetivo es el protocolo, y cada corrida cuesta unas
6–8 horas de calificación manual.

## 4. Posicionamiento frente a la literatura (matriz v4)

Siguiendo su observación, no presento "localizar el origen de los errores" como novedad: RAGChecker ya atribuye por afirmación al
recuperador o al generador. Lo que propongo como diferencia, y que la matriz muestra fila por fila, es:

1. La **cobertura del corpus por pregunta (N0) como condición previa**: ninguna de las ocho métricas registra si la información
   existía, por lo que confunden "no llegó" con "no existía" y no pueden definir la abstención debida. RGB mide el rechazo solo en
   el caso extremo (ningún documento útil) y con documentos manipulados, sin recuperador real.
2. **Varios fallos registrados en la misma respuesta** con la referencia por hechos que los separa (p. ej. n07 RAG: E1 + E3).
3. **Las citas como último eslabón de esa misma cadena**, en la misma tabla por afirmación, con la distinción cita incorrecta /
   hecho omitido / correcto sin respaldo que ALCE y CiteEval no hacen.
4. Dominio técnico cerrado (ATT&CK) y español, donde ninguna de las ocho se valida.

## 5. Limitaciones que declararé

- **Muestra**: 31 preguntas, 62 respuestas, un evaluador principal, un segundo evaluador en 4 preguntas. Todo es descriptivo.
- **Un solo modelo y configuración** (qwen3:4b-instruct, granite-embedding:30m, híbrido RRF, top_k = 5, CPU). No se comparan
  sistemas; se demuestra el protocolo.
- **Generación no determinista con temperatura 0**: dos corridas del mismo conjunto recuperaron contextos idénticos y generaron
  respuestas distintas en 19/36. La traza es el único registro de lo que se calificó.
- **Extracción de afirmaciones**: en el piloto la hizo el evaluador principal; en la corrida 2 fue asistida (sin juicio) y revisada
  por él. El segundo evaluador juzgó afirmaciones ya extraídas. La unidad de calificación no la fija el evaluador independiente.
- **Referencia cerrada al corpus**: una negación verdadera en el mundo pero ajena al corpus (n15 técnica retirada, n18 D3FEND)
  se calificó como abstención correcta si es verdadera y como hecho INCORRECTA si es falsa ("T1486 no existe").
  **[decisión]** ¿Mantiene esta regla o prefiere que toda afirmación en pregunta nula cuente como NO-ABS, como en el piloto?
- **Corpus**: solo Enterprise v19.2; Mobile e ICS no ingestados (por diseño, para tener preguntas nulas controladas).
- **Idioma**: 16 es / 2 en en la corrida 2 (solo como referencia); el estudio del idioma queda fuera del alcance.

## 6. Trabajo futuro (fuera del alcance, D8)

Módulo de evaluación y auditoría continua (`grade()` como función pura sobre las tablas, alertas configurables, CLI/API);
extracción de afirmaciones por un LLM distinto del generador con revisión humana; validación de la extracción y de la tabla de
hechos con segundo evaluador; efecto del idioma con preguntas equivalentes; corpus multi-dominio.

## 7. Plan para cerrar

| Semana | Hito | Necesito de usted |
|---|---|---|
| 1 | Cerrar las dos decisiones de §3 y §5 y la estructura del documento final | reunión de 30 min o respuesta por correo |
| 2 | Capítulo de evaluación (este borrador ampliado con tablas y figuras) + capítulo de diseño del protocolo | — |
| 3 | Capítulos de introducción, estado del arte (matriz v4) y conclusiones; revisión completa | lectura del borrador |
| 4 | Correcciones y versión para defensa | fecha de defensa **[decisión]** |

Quedo atento a sus comentarios. Todo el material (código, corridas, calificaciones y protocolo) está en el repositorio en la
rama `main`.
