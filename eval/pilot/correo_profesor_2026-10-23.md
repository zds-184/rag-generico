**Asunto:** Avance del protocolo de evaluación — estado al 23 de octubre y repositorio

Estimado profesor:

Como no pudimos reunirnos, le envío por escrito lo que tengo hasta el momento, organizado según los cinco puntos que me indicó, y al final las decisiones que necesitaría de su parte para cerrar el protocolo.

**Repositorio:** https://github.com/zds-184/rag-generico (rama `main`). Todo lo que menciono está en la carpeta `eval/pilot/`; indico la ruta de cada archivo.

---

## 1. Qué se califica (rúbrica por afirmación)

Ya está definida y aplicada. Cada respuesta se descompone en afirmaciones y cada una se juzga en dos ejes independientes: corrección frente a la referencia (`CORRECTA` / `INCORRECTA` / `FUERA_REF`) y respaldo en los fragmentos recibidos (`SOSTENIDA` / `CITA-X` / `SIN-CITA` / `SIN-RESPALDO`, solo en modo RAG). Con eso se distinguen las tres situaciones que usted pidió separar: incorrecta, incompleta (omisión de hechos de la referencia) y correcta sin respaldo. Las notas 0/1/2 (N2, N3) ahora se derivan de la tabla y una respuesta puede llevar varias causas a la vez (E0–E3), no solo el primer eslabón.

La cobertura del corpus se mantiene como condición de referencia: lo que no está en la referencia es `FUERA_REF`, no incorrecto, y lo que se afirma sin base sobre la parte no respondible se registra aparte como `NO-ABS`.

- Protocolo consolidado: `eval/pilot/protocol_v2.2.md` (§3).
- Calificación completa de las 26 respuestas del piloto (13 preguntas × RAG/LLM, 92 afirmaciones): `eval/pilot/v2/calificacion_v2.xlsx`.

## 2. Recuperación y citas

N1 se calcula por hecho de la referencia, no por fragmento gold: para cada hecho se registra si llegó evidencia gold, alternativa (`ALT`), parcial (`ALT-P`) o ninguna, y la pregunta queda en NINGUNA / PARTE / TODA. Esto cambió el diagnóstico de varios casos: en p05 no llegó ningún gold pero sí evidencia alternativa para 2 de 4 hechos; en p09 llegó el gold pero solo 2 de 6 hechos.

Las citas se revisan siempre, también en respuestas incorrectas, con la regla "el fragmento debe expresar la relación, no solo nombrar las entidades". Los dos casos que usted señaló quedaron así:
- **p05 (APT29/Mimikatz):** "APT29 utiliza Mimikatz" es correcta frente a la referencia pero ningún fragmento la sostiene (los dos nombres aparecen en la misma lista sin vínculo) → `SIN-RESPALDO`. Diagnóstico E1 + E2 + E3.
- **p09 (mitigaciones de Phishing):** la respuesta niega que haya mitigaciones aunque el fragmento 5 traía M1054 y M1047 → abstención errónea (`ABS-E`), diagnóstico E1 + E2 en lugar de solo E1.

- Reglas: `protocol_v2.2.md` §4. Evidencia por hecho: `eval/pilot/evidence_pilot.json`, `evidence_check.py`, resultado en `results/20260922_064359/n1_v2.json`.

## 3. Comparación con y sin RAG

La diferencia de N2 entre modos deja de ser el titular. Ambos modos se comparan contra la misma referencia cerrada al corpus y se reportan cuatro lecturas separadas: (A) fidelidad a la referencia, (B) abstención, (C) respaldo documental (solo RAG) y (D) contenido fuera de la referencia. Resultado sobre las 26 respuestas:

| Lectura | RAG | LLM |
|---|---|---|
| A. Hechos de la referencia cubiertos | 10/33 (30 %) | 11/33 (33 %) |
| A. Afirmaciones incorrectas ÷ afirmaciones de hecho | 19 % | 18 % |
| B. Respuestas con abstención errónea (ABS-E) | 3 | 1 |
| B. Respuestas que afirman sin base (NO-ABS) | 0 | 7 |
| C. Precisión de citas | 71 % | N/A |
| C. Cobertura de citas (hechos cubiertos y citados) | 27 % | N/A |
| D. Afirmaciones fuera de la referencia | 2 | 32 |

Es decir: frente a la referencia, ambos modos cubren una proporción similar de hechos; la diferencia real está en que el LLM responde sin base en 7 de 13 preguntas (las no respondibles y las partes no respondibles) y añade mucho contenido fuera de la referencia, mientras que el RAG se abstiene de más (a veces erróneamente, 3 casos). Sin pruebas de significancia por el tamaño de la muestra.

- `protocol_v2.2.md` §5; hoja `Resumen` de `calificacion_v2.xlsx`.

## 4. Validación y posicionamiento

**Segundo evaluador.** Un evaluador independiente calificó, a ciegas y sin ver mis notas, las 4 preguntas acordadas (p01, p05, p06, p09; 8 respuestas, 27 afirmaciones). Las afirmaciones ya estaban extraídas en la plantilla; él juzgó tipo, corrección, hecho cubierto y respaldo.

| Medida | Acuerdo |
|---|---|
| Corrección (`vs_ref`) | 23/27 (85 %), kappa de Cohen 0,78 |
| Tipo (hecho / abstención) | 26/27 (96 %), kappa 0,89 |
| Respaldo | 4/5 pares comparables |
| N2 por respuesta | 7/8 |
| Diagnóstico (lista de causas) | 7/8 |

Los 7 desacuerdos no son errores de lectura sino tres puntos donde la rúbrica admite dos interpretaciones. Los detallo en la sección de decisiones, porque son lo que necesito acordar con usted.

- Libro del evaluador 2: `eval/pilot/v2/calificacion_v2_eval_independent.xlsx`.
- Calificación exploratoria con Claude (modelo, instrucciones y evidencia disponible guardados, sin mostrarle mis notas): `eval/pilot/ejemplos_calificados_v2.md`.

**Matriz comparativa.** Ampliada con ALCE (Gao et al., EMNLP 2023) y CiteEval (Xu et al., ACL 2025), leídos en los PDF. La diferenciación ya no se apoya en "las citas no se han estudiado", sino en el diagnóstico encadenado corpus → recuperación → generación → citas, con referencia por hechos y registro de abstención; de ALCE se reutiliza la unidad de enunciado y la distinción cita que sostiene / que no; de CiteEval, juzgar contra el contexto completo y no solo lo citado. Adjunto `matriz_comparativa_evaluacion_RAG_v3.xlsx` (no está en el repositorio).

- `protocol_v2.2.md` §7.1–7.2.

**Ejemplos calificados por afirmación** (los tres o cuatro que me pidió): p05, p09, p01 y p06, en ambos modos, con la tabla por afirmación, el diagnóstico y los puntos a discutir en cada uno: `eval/pilot/borrador_ejemplos_reunion.md`.

## 5. Corrida reproducible

Pendiente a propósito, para no mover la referencia del piloto antes de cerrar la rúbrica. Los requisitos están fijados en `protocol_v2.2.md` §8: corregir el solape duplicado del chunking y reingerir, comprobar la ingesta completa, impedir que los scripts sobrescriban calificaciones (hoy `build_calificacion_v2.py` ya se niega; `run_pilot.py --rebuild-xlsx` todavía no), impedir que `--resume` mezcle configuraciones, y conservar manifest del corpus, textos gold y límites de generación. Se mantiene top_k = 5 y el mismo modelo. El piloto original (`protocol.md`, `questions.jsonl`, `results/20260922_064359/`) sigue intacto.

Después de cerrar la rúbrica propondré el conjunto nuevo de preguntas, equilibrado por cobertura del corpus (completa / parcial / nula).

---

## Decisiones que necesito de su parte

Son las tres reglas que explican los desacuerdos con el evaluador 2. En cada una indico las dos lecturas y la que propongo.

**D1. Afirmaciones sobre la parte no respondible.** Ejemplo p06: la pregunta incluía "ataques de Lazarus contra Ecuador" (no está en el corpus) y el sistema responde "No hay referencia a ataques contra Ecuador". Yo lo marqué `FUERA_REF` (no está en la referencia); el evaluador 2 lo marcó `CORRECTA` (se abstuvo como debía). Explica 4 de los 7 desacuerdos.
*Propuesta:* si es una **abstención** ("no hay referencia en los pasajes") → `CORRECTA`, se mide en la lectura B y no cuenta para N2; si es un **hecho** afirmado sobre la fuente ("MITRE no recomienda ningún producto") → `FUERA_REF` + `NO-ABS`. Con esa regla, dos de los cuatro casos quedan como los calificó cada evaluador, lo que sugiere que el problema era la regla y no los evaluadores.

**D2. Abstención vs. afirmación de ausencia.** Ejemplo p06 LLM: "ATT&CK no documenta que Lazarus use sub-técnicas T1059.*". Yo: `hecho` incorrecto (afirma algo falso sobre ATT&CK). Evaluador 2: `abstención`. La regla ya existe en §3.2 (sujeto = la fuente → hecho; sujeto = el contexto o el modelo → abstención), pero no fue visible para él.
*Propuesta:* mantener la regla y añadirla a la guía del Excel con los dos ejemplos literales. No cambia el diagnóstico (ambos van a E2 y alerta CRITICA), solo el código.

**D3. Hecho cubierto pero negado en la misma respuesta.** Ejemplo p09 RAG: dice "los pasajes no listan mitigaciones" y a continuación "los pasajes mencionan SPF, DKIM y DMARC" (que es la mitigación M1054). Yo conté M1054 como cubierto (N2 = 1, con alerta CRITICA por la negación); el evaluador 2 no (N2 = 0).
*Propuesta:* contar la cobertura afirmación por afirmación y registrar la negación como `ABS-E`, en línea con la decisión "sin topes" y con su indicación de permitir varios errores en una respuesta. Un 0 ocultaría que el fragmento llegó, se leyó y se citó bien.

**Otros dos puntos:**
- **D4. RQ6 (consistencia):** ¿aprueba que la validación quede como acuerdo entre dos evaluadores en 4 preguntas (descriptivo, con sus límites declarados) más la comparación exploratoria con un LLM, o prefiere que añada una re-calificación a ciegas mía?
- **D5. Alcance de la propuesta de evaluación final:** ¿la centro en el protocolo diagnóstico aplicado a la siguiente corrida, o incluyo también el diseño del módulo de evaluación continua (paquete/CLI sobre la función `grade()`) como trabajo futuro?

Con sus respuestas aplico las reglas a las 26 respuestas, recalculo el acuerdo, cierro el protocolo v2.3 (§7.3 validación y §8 corrida) y le envío la propuesta de evaluación final.

Quedo atento a su disponibilidad para la reunión.

Saludos cordiales,
Darwin Simba
