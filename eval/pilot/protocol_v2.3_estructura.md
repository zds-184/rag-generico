# Protocolo v2.3 — estructura propuesta

**Estado: esquema, no texto final.** Cada sección indica su origen en `protocol_v2.2.md` (que queda intacto) y qué le falta.
La versión 2.3 se escribirá sobre este esquema cuando se decidan los puntos de la sección 3 y llegue la validación.

Cambios frente a v2.2: §7.3 (validación) y §8 (corrida reproducible) dejan de estar vacíos; §1 incorpora el estado de RQ6;
se separa la rúbrica (congelada) de la política y de las reglas de decisión; se añade un registro de versiones.

---

## 0. Control de versión y alcance
- Versión, fecha y qué cambia respecto de v2.2. Origen: tabla de versiones de v2.2.
- Qué queda congelado para la comparación con el piloto (`20260922_064359`, `protocol.md` y `questions.jsonl`).
- **Nuevo:** hash o fecha del corpus (manifest), versión de la rúbrica y versión de la política de alertas en cada resultado.

## 1. Pregunta de investigación
- RQ1–RQ6 de v2.2 §1 sin cambios.
- **RQ6 queda marcada como "pendiente de aprobación del director"** hasta que se decida.

## 2. Diseño del piloto
- Origen: v2.2 §2. Sin cambios. Solo se referencia el piloto; no se recalifica.

## 3. Rúbrica de calificación (núcleo, congelado en v2.3)
- §3.1 Hechos, §3.2 Afirmaciones, §3.3 Códigos, §3.4 Notas derivadas, §3.5 Diagnóstico. Origen: v2.2 §3.
- **Reglas de decisión que hay que cerrar antes de congelar:**
  - ALT-P como "llegó" o no (v2.2 §4.1, punto 4).
  - Afirmación laxa que cubre un hecho de forma indirecta (p01, afirmación 5).
  - Negación de un hecho que sí llegó: ¿E2 o ABS-E? (p09).
  - Conclusión final "no se puede determinar" con hechos correctos en el cuerpo (p06).
- Los ejemplos de la reunión (`borrador_ejemplos_reunion.md`) sirven de casos de referencia para estas reglas.

## 4. Política de alertas (separada de la medición)
- §3.6 de v2.2. Política por defecto: `CRITICA`, `RESPALDO`, `TRUNC`.
- **Pendiente de decisión** (ver §11 de este esquema): mantener, ajustar o retirar.

## 5. Recuperación (N1) y citas
- §4.1 N1 por evidencia, §4.2 reglas de cita, §4.3 métricas. Origen: v2.2 §4.
- **Pendiente:** decidir §6.2 (desempate determinista) antes de la corrida.

## 6. Comparación con y sin RAG
- §5.1 a §5.4 de v2.2: lecturas A–D, estados de abstención, reporte sin pruebas de significancia, herramientas.
- Sin cambios de contenido; solo se añade que la comparación usa la misma referencia cerrada al corpus.

## 7. Validación y posicionamiento
- **7.1 Matriz comparativa** (ALCE, CiteEval, RAGAS, RAGChecker, ARES, FActScore, RefChecker). Origen: v2.2 §7.1 y
  `matriz_comparativa_evaluacion_RAG_v3.xlsx`. Sin cambios.
- **7.2 Diferenciación de la contribución.** Origen: v2.2 §7.2. Sin cambios.
- **7.3 Validación de consistencia (nuevo contenido).** Esquema:
  1. Evaluador 2 (independiente): 4 preguntas, p01, p05, p06 y p09, 8 respuestas. Calificadas a ciegas, sin ver las notas de
     la primera evaluación.
  2. Métricas de acuerdo por afirmación:
     - kappa de Cohen (o α de Krippendorff) para `vs_ref` y para `respaldo`;
     - acuerdo N2 y N3 derivados (coincidencia exacta y ±1);
     - acuerdo en los códigos E0–E3 y en las alertas.
  3. Análisis de desacuerdos: tabla caso por caso con la causa (regla ambigua, interpretación de la evidencia, error de
     transcripción).
  4. Resultado del análisis: qué reglas se ajustan y cuáles se dejan documentadas como límite.
  5. Protocolo de la calificación de Claude (exploratoria, no sustituye la validación): modelo, instrucciones, evidencia
     disponible. Sin mostrarle las calificaciones humanas.
  - **Estado: pendiente de recibir el documento del evaluador 2.**
- **7.4 (nuevo) Límites de la validación:** 4 preguntas y 8 respuestas; el acuerdo tiene poca potencia estadística y se
  reporta como descriptivo.

## 8. Corrida reproducible (nuevo contenido, después de la reunión)
Requisitos ya fijados en v2.2 §8; se convierten en criterios de aceptación:
1. Corregir el solape duplicado del chunking (`app/rag/chunking.py`) y reingerir.
2. Comprobar que la ingesta esté completa (puntos esperados frente a la colección).
3. Proteger las calificaciones: ningún script sobrescribe un libro existente. Hoy `run_pilot.py --rebuild-xlsx` sí lo hace.
4. `--resume` no mezcla configuraciones: compara `config.json` y se niega si cambia.
5. Conservar manifest del corpus, textos gold y límites `LLM_NUM_CTX` / `LLM_NUM_PREDICT`.
6. Piloto original intacto.
7. Conjunto nuevo de preguntas: equilibrado por cobertura del corpus (completa, parcial, nula), viable de calificar con la
   tabla por afirmación. Se propone después de cerrar la rúbrica.
- **Estado: pendiente de decisión** (ver §11 de este esquema).

## 9. Resultados del piloto
- Origen: v2.2 §9. Sin cambios. Se conserva la comparación piloto → v2 (`ejemplos_calificados_v2.md`).

## 10. Casos ambiguos y su resolución
- Origen: v2.2 §10. Se añade una columna "decisión" que se rellena con lo que se resuelva en la reunión.

## 11. Decisiones pendientes (de la reunión y de la validación)
| # | Decisión | Opciones | Estado |
|---|---|---|---|
| D1 | ALT-P cuenta como "llegó" | No (estricto, v2.2) / Sí | pendiente |
| D2 | Afirmación laxa que cubre un hecho (p01/5) | CORRECTA / FUERA_REF | pendiente |
| D3 | Negación de hechos que llegaron (p09) | E2 solo / ABS-E + E2 | pendiente |
| D4 | Peso del veredicto final en p06 | sin topes (v2.2) / tope | pendiente |
| D5 | Política de alertas | mantener / ajustar / retirar | pendiente |
| D6 | Desempate en la recuperación (§6.2) | corregir antes de la corrida / documentar | pendiente |
| D7 | RQ6 y juez exploratorio | aprobado / no aprobado | pendiente del director |
| D8 | Alcance de la propuesta final | protocolo diagnóstico / + módulo de auditoría | pendiente |

## 12. Entregables de la reunión (referencia)
- Protocolo v2.3 (este documento, completo).
- Ejemplos: `borrador_ejemplos_reunion.md` (4 casos).
- Propuesta de evaluación final (entregable 8, sin empezar).

## Anexos
- A. Rúbrica v1.1 original (comparabilidad). Origen: v2.2 Anexo A.
- B. Correspondencia v1.1 → v2. Origen: v2.2 Anexo B.
- C. Archivos del proyecto. Origen: v2.2 Anexo C, añadiendo `borrador_ejemplos_reunion.md` y este esquema.
