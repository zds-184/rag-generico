# Corrida 2 — propuesta del conjunto de preguntas

**Estado: propuesta (2026-10-30), pendiente de validación por el evaluador principal y de la reingesta.**
Rúbrica: `eval/pilot/protocol_v2.3.md` (congelada). Configuración: la del piloto (`qwen3:4b-instruct`, `granite-embedding:30m`,
híbrida RRF, `top_k=5`, `LLM_NUM_CTX=4096`, `LLM_NUM_PREDICT=1024`). Lo único que cambia frente al piloto es el conjunto de
preguntas y el corpus reingestado (chunking corregido, desempate determinista).

Archivos:
- `questions_propuesta.jsonl`: 18 preguntas con `reference`, hechos `H#` (`facts`), `unanswerable_part`, `priority` (`core` /
  `ext`) y `gold_evidence` (fragmentos literales del corpus que enuncian cada hecho). `gold_point_ids` vacío a propósito.
- `fill_gold.py`: tras la reingesta, localiza los chunks que contienen cada fragmento y escribe `questions.jsonl` con los
  `gold_point_ids` del corpus nuevo y la huella del manifest. `--check` solo comprueba.

## 1. Criterios de diseño

1. **Equilibrio por cobertura del corpus (N0):** 6 completas, 6 parciales, 6 nulas. El piloto tenía 5 / 4 / 4.
2. **Dos tamaños.** `core` = 12 preguntas (4 + 4 + 4, 25 hechos); `ext` = 6 más (42 hechos en total). Se corre todo (el costo
   de máquina es bajo: ~18 × 2 × 3 min ≈ 2 h) y se califica primero el `core`; las `ext` se califican si queda tiempo.
   Estimación de calificación manual: 10–15 min por respuesta RAG, 5–10 por respuesta LLM → `core` ≈ 4–5 h, todo ≈ 7–8 h.
3. **Sin reutilizar objetos del piloto** (T1059.001, T1566, TA0003, S0154, G0016/S0002, G0032, T1110.003/G0007). Lazarus
   reaparece solo como atribución de la campaña C0022 (n09, `ext`).
4. **Tipos de objeto nuevos:** campaña (C0028, C0022), mitigación como objeto (M1032), táctica (TA0010, TA0040), herramienta
   (S0363), grupo (G0096), técnica/sub-técnica (T1486, T1021.001, T1003.001).
5. **Hechos verificados contra `data/documents.jsonl`** (texto por documento, estable frente a la reingesta): cada `H#` tiene un
   fragmento literal en `gold_evidence` que el script comprobó (18/18 OK el 2026-10-30). Los `point_id` se asignan después.
6. **Cada pregunta es espejo de una del piloto o de una categoría nueva**, para que la comparación piloto ↔ corrida 2 sea por
   tipo de pregunta y no por pregunta.
7. **Idioma:** 16 es / 2 en (n05 y n14, ambas de extensión, solo como referencia). El 2026-11-05 se reformularon al español n03, n08, n11, n16 y n18 (mismos hechos y gold) porque el estudio del idioma queda fuera del alcance; la corrida `20261104_084930` (11 es / 7 en) se conserva como réplica.

## 2. Las 18 preguntas

| id | prio | cob. | lang | objeto | dificultad de recuperación | H | parte no respondible | espejo de |
|---|---|---|---|---|---|---|---|---|
| n01 | core | completa | es | TA0010 Exfiltración | single-chunk-conceptual | 4 | — | p03 |
| n02 | core | completa | es | T1486 mitigaciones | deep-chunk (5/11) | 4 | — | p01 |
| n03 | ext | completa | es | T1021.001 mitigaciones | deep-chunk, lista cerrada de 8 (3–4/8) | 8 | — | p01 (lista larga) |
| n04 | core | completa | es | C0028 campaña Ucrania 2015 | single-chunk (campaña) | 4 | — | nuevo (campaña) |
| n05 | ext | completa | en | S0363 Empire | single-chunk | 4 | — | p04 (software) |
| n06 | core | completa | es | G0096 APT41 + S0363 | multi-object (dos documentos) | 3 | — | p05 |
| n07 | core | parcial | es | T1003.001 LSASS | deep-chunk (1 y 3/10) | 2 | producto EDR recomendado | p09 |
| n08 | core | parcial | es | M1032 MFA | single-chunk | 4 | % de robos de cuenta evitados | p09 **invertida** (los productos SÍ están) |
| n09 | ext | parcial | es | C0022 Operation Dream Job | single-chunk (campaña) | 3 | víctimas en América Latina | p06 |
| n10 | core | parcial | es | TA0040 Impacto | single-chunk-conceptual | 2 | técnica más usada en Ecuador 2025 | p03 + p08 |
| n11 | core | parcial | es | S0363 "Used by" (G0034, G0010) | deep-chunk (4/4), multi-object alt. | 2 | año de adopción | p06 |
| n12 | ext | parcial | es | T1486 descripción | two-contiguous-chunks (1 y 3/11) | 2 | familia de ransomware más usada | p04 |
| n13 | core | nula | es | T1636.003 (Mobile) | out-of-ingested-domain | 0 | todo | p10 |
| n14 | ext | nula | en | T0831 (ICS) | out-of-ingested-domain | 0 | todo | p11 |
| n15 | core | nula | es | T1064 Scripting (retirada) | **deprecated-object** | 0 | todo | nuevo |
| n16 | core | nula | es | T1021.009 (inventado) | fabricated-id | 0 | todo | p13 |
| n17 | ext | nula | es | ransomware Ecuador 2025 | out-of-scope-knowledge | 0 | todo | p12 |
| n18 | core | nula | es | D3FEND ↔ T1486 | **adjacent-mitre-knowledge** | 0 | todo | nuevo |

Texto completo, referencias y hechos: `questions_propuesta.jsonl`.

## 3. Qué mide cada bloque (ligado a las lecturas A–D de §5)

- **Completas:** fidelidad (lectura A) y citas (C). n02 y n03 miden omisión en listas cerradas con el chunk gold profundo;
  n06 mide si el top-5 se reparte entre dos documentos (el fallo E1 más frecuente del piloto, p05).
- **Parciales:** abstención debida (lectura B). n08 es la inversión de p09: en el piloto el producto comercial no estaba en el
  corpus; aquí Azure AD / Okta / AWS IAM sí están en M1032, así que abstenerse es `ABS-E`. n11 pone la parte respondible en el
  último chunk de un documento largo.
- **Nulas:** `NO-ABS` frente a abstención. Dos categorías nuevas:
  - n15 (**técnica retirada**): T1064 existió y el LLM la conoce; la ingesta excluye objetos `revoked`/`deprecated`, así que
    no está en el corpus. Con la referencia cerrada al corpus, responder es `NO-ABS` aunque lo dicho sea históricamente cierto.
    Hay que presentarlo al director como caso límite: mide si el RAG se ciñe a los pasajes (que traerán T1059.*) o responde de
    memoria.
  - n18 (**conocimiento MITRE adyacente**): D3FEND no está en el STIX de ATT&CK (la cadena no aparece en el corpus). La
    recuperación traerá T1486 (relevante pero sin la respuesta): mide si el modelo presenta las mitigaciones ATT&CK como si
    fueran contramedidas D3FEND.
- **Distractores reales en el corpus:** n10 y n17 mencionan Ecuador; el corpus lo nombra una vez (T1480, APT-C-36 / G0099) y
  puede llegar al top-5. n12 y n18 recuperan T1486 con sus procedure examples (muchas familias de ransomware).

## 4. Notas de calificación anticipadas (para no reabrir reglas)

- **Listas cerradas** (n03: 8 mitigaciones; n07: 4 SSP; n09: 5 países): un ítem omitido es `OMI`; un ítem extra es `FUERA_REF`
  (§3.2), no `INCORRECTA`. En n07 y n09 la lista completa es **un** hecho (H2 / H3): se marca `CORRECTA` solo si enuncia la
  lista entera; si falta un ítem, la afirmación es `FUERA_REF` por la regla D2 y el hecho queda `OMI`. Si el evaluador prefiere
  un hecho por ítem, se decide antes de calificar y se aplica a todo el conjunto.
- **n05, H2/H3** (framework en Python, agentes en PowerShell/Python): "Empire está escrito en PowerShell" contradice H2 →
  `INCORRECTA`.
- **n06, H3:** la evidencia puede llegar por G0096 (sección *Software used*) o por S0363 (*Used by*); ambas son `gold`
  (`fill_gold.py` marca las dos).
- **n11:** evidencia alternativa en G0034 y G0010 (sección *Software used*) → `ALT`, cuenta como "llegó".
- **n15 y n18:** cualquier afirmación de hecho es `NO-ABS` (H = 0). Se reportan aparte como "nula fuera del corpus pero dentro
  del conocimiento del LLM" para la discusión con el director.

## 5. Pasos

1. Evaluador principal: leer las 18 referencias y hechos contra ATT&CK (web o `documents.jsonl`) y corregir lo que haga
   falta; cambiar `status` a `final`. Decidir si el `core` basta.
2. Reingesta (`FORCE_REINGEST=true`), `check_ingest.py`, luego `python eval/run2/fill_gold.py` → `eval/run2/questions.jsonl`.
3. Corrida: `python eval/pilot/run_pilot.py --questions eval/run2/questions.jsonl --top-k 5` (carpeta nueva en
   `eval/pilot/results/`); después `--check-ties` sobre esa carpeta.
4. Calificación manual con la plantilla v2.3 (`core` primero), lecturas A–D, tabla de diagnósticos, comparación con el piloto
   por tipo de pregunta.
