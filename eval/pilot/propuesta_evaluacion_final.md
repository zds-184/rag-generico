# Propuesta de evaluación final 

**Estudiante:** Darwin Simba · **Fecha:** 2026-11-08 · **Estado:** v0.2, con la respuesta del director del 2026-11-10 incorporada (§9 del protocolo v2.3); cifras actualizadas el 2026-11-24 tras las observaciones del director al documento (protocolo §5.4.4 y §7.3)
**Repositorio:** https://github.com/zds-184/rag-generico · **Documentos base:** `eval/pilot/protocol_v2.3.md` (rúbrica congelada),
`matriz_comparativa_evaluacion_RAG_v4.xlsx` (posicionamiento), `eval/pilot/v2/calificacion_v2.xlsx` (piloto) y
`eval/run2/calificacion_v2_run2.xlsx` (corrida 2).

A continuación presento cómo propongo cerrar la evaluación del proyecto. Sigo el orden que acordamos el 29 de octubre: rúbrica
congelada, corrida reproducible y, ahora, la propuesta final. Las marcas **[decisión]** de la v0.1 quedan resueltas con su respuesta del 2026-11-10 y se indican como **[resuelto]**.

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
| RQ1 | ¿Existía la información en el corpus? | 31 preguntas en dos conjuntos (completas 11, parciales 10, nulas 10), cada referencia verificada literalmente en el corpus; categorías nuevas en la corrida 2: técnica retirada (n15) y conocimiento MITRE adyacente (n18) | N0 es una condición del protocolo, no un resultado: se fija por diseño y queda registrado por pregunta, cosa que ninguna de las ocho métricas de la matriz hace |
| RQ2 | ¿La recuperación trajo la evidencia? | `llegó` por hecho leído en los contextos; gold en el top-5 en 6/9 (piloto) y 10/12 (corrida 2) preguntas respondibles; desempate determinista verificado en vivo (D6) | Sí, por hecho y aceptando evidencia alternativa; la lectura por hecho atribuye a la recuperación al menos un fallo en 9 respuestas RAG (p01, p02, p05, p08, p09; n02, n03, n07, n12) |
| RQ3 | ¿Cada afirmación es correcta, completa y fiel? | 234 afirmaciones calificadas (92 piloto + 142 corrida 2) | Sí; la regla de enunciación (D2) es la que más decisiones resuelve |
| RQ4 | ¿Cada afirmación está sostenida por su cita? | precisión de citas 71 % (piloto) y 74 % (corrida 2); cobertura de citas 39 % → 55 %; códigos CITA-X / SIN-CITA | Sí; el defecto dominante es distinto en cada corrida: CITA-X en el piloto (4 frente a 1) y SIN-CITA en la corrida 2 (9 frente a 1: listas sin [n]) |
| RQ5 | ¿En qué se diferencian con y sin recuperación? | Lecturas A–D en ambas corridas (tabla §3) | El RAG cubre más hechos (42 % y 64 % frente a 24 % y 17 %), no responde sin base (NO-ABS 0 frente a 6 y 7, es decir 13 de 20; los dos modos usan instrucciones distintas, así que la diferencia no mide solo la recuperación) y su coste es la abstención errónea (ABS-E 3 y 4): de las 7, en 4 ningún hecho negado había llegado (E1), en 1 habían llegado todos (E2) y en 2 se juntan las dos causas |
| RQ6 | ¿Es consistente entre evaluadores? | Segundo evaluador independiente en 4 preguntas / 27 afirmaciones: acuerdo bruto `vs_ref` 23/27 (κ 0,78) y `tipo` 26/27 (κ 0,89), con las calificaciones tal como se entregaron el 2026-10-23. Aparte, como adjudicación y no como acuerdo: 26/27 tras aplicar las reglas congeladas a ambas calificaciones | Sí en lo esencial, con el acuerdo bruto como respuesta; los 4 desacuerdos de `vs_ref` eran una sola regla (parte no respondible): v2.2 la tenía escrita de una forma, el segundo evaluador la aplicó y D2 la cambió después. Límite: afirmaciones pre-extraídas, muestra pequeña, un evaluador adicional |

## 3. Resultados que propongo reportar (descriptivos, sin pruebas de significancia)

| Lectura | Piloto RAG | Piloto LLM | Corrida 2 RAG | Corrida 2 LLM |
|---|---|---|---|---|
| A. Hechos cubiertos | 14/33 (42 %) | 8/33 (24 %) | 27/42 (64 %) | 7/42 (17 %) |
| A. Afirmaciones INCORRECTA | 19 % (4/21) | 25 % (13/53) | 0 % (0/38) | 28 % (22/80) |
| B. Respuestas con ABS-E | 3 | 0 | 4 | 0 |
| B. Respuestas con NO-ABS | 0 | 6 | 0 | 7 |
| C. Precisión / cobertura de citas | 71 % / 39 % | — | 74 % / 55 % | — |
| C. SIN-R / CITA-X / SIN-C | 1 / 4 / 1 | — | 0 / 1 / 9 | — |
| D. Afirmaciones FUERA_REF | 3 | 31 | 10 | 53 |
| N2 promedio | 1,38 | 0,46 | 1,61 | 0,28 |
| Respuestas OK | 7 | 1 | 9 | 1 |
| Diagnóstico más frecuente (respuestas con la etiqueta) | E1 (5) | E2 (9) | E3 (6), E1 (4) | E2 (12), E0 (7) |

Las dos corridas se presentan como **dos aplicaciones de la misma rúbrica**, no como un antes y un después del sistema. Entre
ellas cambiaron el conjunto de preguntas, la fragmentación y el desempate (reingesta de 7 241 a 7 244 fragmentos) y la forma de
calificar, porque la corrida 2 pasó por una revisión asistida. La diferencia en INCORRECTA del RAG (19 % → 0 %) no se explica
solo por el conjunto: mi calificación original de la corrida 2 tenía 16 % y el 0 % aparece con la revisión. Lo que propongo
como hallazgo: (a) el RAG no responde sin base y el LLM lo hace en 9 de las 10 nulas, con la salvedad de que los dos modos usan
instrucciones distintas; (b) cuando el RAG falla, el protocolo separa si fue la recuperación (E1), la generación (E2) o ambas;
(c) el defecto de citas dominante cambia de corrida a corrida (CITA-X en el piloto, SIN-CITA en la corrida 2) y las
afirmaciones sin ningún respaldo son 1 y 0.

**[resuelto]** No hay tercera corrida (director, 2026-11-10): dos conjuntos bastan para mostrar el protocolo.

**Revisión asistida de la calificación de la corrida 2.** La calificación manual pasó por una revisión propuesta por el asistente
(67 cambios en 48 de 142 afirmaciones; todos aceptados por mí, `SI` en la hoja `Revisión`). Entre mi calificación y la final el
RAG pasa de 57 % a 64 % de hechos cubiertos, de 16 % a 0 % de `INCORRECTA`, de 0 a 4 respuestas con `ABS-E` y de 1 a 0 con
`NO-ABS`; el LLM de 26 % a 27 % de `INCORRECTA` y mantiene 8 `NO-ABS`. La misma hoja llenó los 42 valores de `llegó`, que en mi
calificación estaban vacíos y de los que dependen todos los E1 y E2 de la corrida 2; la columna de aceptación la llené el
2026-11-10. Las causas son dos reglas aplicadas de forma uniforme: extras de lista que no
contradicen la referencia son `FUERA_REF`, y "los contextos no mencionan…" es una abstención, que al negar un hecho que la
referencia contiene se registra como `ABS-E`. El detalle, tabla completa y límite (el mismo asistente extrajo y revisó) están en
el protocolo §5.4.1.

**Revisiones de coherencia (2026-11-17 y 2026-11-24).** La regla de la parte no respondible y la de las negaciones sobre objetos
fuera del corpus no se habían aplicado igual en las dos corridas. Se unificaron en dos pasos, propuestos por un asistente y
aceptados por mí, registrados en las hojas `Revisión 2026-11-17` y `Revisión 2026-11-24` de los dos libros (protocolo §5.4.3 y
§5.4.4). Solo cambian cifras del modo LLM: piloto, `NO-ABS` de 7 a 6, `INCORRECTA` 13/53 (25 %), `FUERA_REF` 31; corrida 2,
`NO-ABS` de 8 a 7 (n17 LLM #1, una negación verdadera sobre la fuente en una pregunta nula, pasa a abstención correcta por D10), `INCORRECTA` 22/80 (28 %), `FUERA_REF` 53. El total de respuestas sin base del LLM queda en 13 de 20.

## 4. Posicionamiento frente a la literatura (matriz v4)

Siguiendo su observación, no presento "localizar el origen de los errores" como novedad: RAGChecker ya atribuye por afirmación al
recuperador o al generador. Lo que propongo como diferencia, y que la matriz muestra fila por fila, es:

1. La **cobertura del corpus por pregunta (N0) como condición previa**: ninguna de las ocho métricas registra si la información
   existía, por lo que confunden "no llegó" con "no existía" y no pueden definir la abstención debida. RGB mide el rechazo solo en
   el caso extremo (ningún documento útil); sus documentos son reales, pero el modelo recibe un conjunto fijo y no recupera.
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
  **[resuelto]** Se mantiene la regla; el capítulo lista los casos donde se aplicó (n15, n18): protocolo §5.4.2.
- **Corpus**: solo Enterprise v19.2; Mobile e ICS no ingestados (por diseño, para tener preguntas nulas controladas).
- **Idioma**: 16 es / 2 en en la corrida 2 (solo como referencia); el estudio del idioma queda fuera del alcance.

## 6. Trabajo futuro (fuera del alcance, D8)

Módulo de evaluación y auditoría continua (`grade()` como función pura sobre las tablas, alertas configurables, CLI/API);
extracción de afirmaciones por un LLM distinto del generador con revisión humana; validación de la extracción y de la tabla de
hechos con segundo evaluador; efecto del idioma con preguntas equivalentes; corpus multi-dominio.

## 7. Plan para cerrar

| Semana | Hito | Necesito de usted |
|---|---|---|
| 1 | (hecho 2026-11-10) Decisiones de §3 y §5 cerradas; estructura del documento final | estructura y fechas, pendientes de su parte |
| 2 | Capítulo de evaluación (este borrador ampliado con tablas y figuras) + capítulo de diseño del protocolo | — |
| 3 | Capítulos de introducción, estado del arte (matriz v4) y conclusiones; revisión completa | lectura del borrador |
| 4 | Correcciones y versión para defensa | fecha de defensa (pendiente) |

Quedo atento a sus comentarios. Todo el material (código, corridas, calificaciones y protocolo) está en el repositorio en la
rama `main`.
