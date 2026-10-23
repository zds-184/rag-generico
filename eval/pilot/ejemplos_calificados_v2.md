# Ejemplos calificados por afirmación (rúbrica `protocol_v2.2.md`)

*Recreado el 2026-10-20 a partir del contenido original (2026-10-12); coincide con `afirmaciones_ejemplos.csv`.*

Corrida `20260922_064359` (no se modifica). Casos: **p05** y **p09** (pedidos por el director), **p01** (recuperación
fallida + respuesta truncada en LLM) y **p06** (el gold llegó pero el modelo se abstuvo). Ambos modos.
Calificadas por Claude como **borrador, pendientes de revisión del evaluador**, sin consultar el Excel del piloto hasta el
final; la comparación está al cierre. Los juicios marcados con ⚠ son los más discutibles y los que conviene revisar primero.

Leyenda: `tipo` h = hecho, a = abstención · `vs_ref` C = CORRECTA, I = INCORRECTA, F = FUERA_REF ·
`respaldo` S = SOSTENIDA, X = CITA-X, SC = SIN-CITA, SR = SIN-RESPALDO.

---
## p05 — APT29 / Mimikatz (es, respondible completa)

**Hechos de la referencia:** H1 APT29 usa Mimikatz · H2 T1550.003 Pass the Ticket · H3 T1558.001 Golden Ticket · H4 T1558.002 Silver Ticket.
**Contexto recibido (RAG):** r1 y r2 = T1550.003 (en r1 aparecen por separado "G0016 APT29: usó ataques de tickets Kerberos
para movimiento lateral" y "S0002 Mimikatz: módulos `KERBEROS::PTT`…"); r3 Kerberoasting; r4 MobileOrder; r5 T1558.001 Golden Ticket
("Mimikatz's kerberos module can create golden tickets").
**`llegó`:** H1 NO (ningún fragmento dice que APT29 use Mimikatz; los dos nombres aparecen en la misma lista, no vinculados) ·
H2 ALT (r1/r2, no gold) · H3 ALT (r5, no gold) · H4 NO. Nota: `gold_points_found` = 0/3, pero hay evidencia alternativa para H2 y H3.

### RAG
| # | Afirmación | tipo | vs_ref | hecho | respaldo | cita → sostiene | Códigos |
|---|---|---|---|---|---|---|---|
| 1 | APT29 (G0016) utiliza Mimikatz | h | C | H1 | **SR** ⚠ | [1] → ninguno | SIN-R |
| 2 | APT29 usó ataques Kerberos para movimiento lateral | h | F | — | S | [1] → r1 | — |
| 3 | Mimikatz implementa T1550.003 Pass the Ticket (módulo KERBEROS::PTT) | h | C | H2 | S | [1] → r1 | — |
| — | OMISION H3 (Golden Ticket) · llegó ALT | | | | | | OMI |
| — | OMISION H4 (Silver Ticket) · llegó NO | | | | | | OMI |

Derivado: C = 2 de 4 (H1, H2), sin INC/ABS-E/NO-ABS → **N2 = 1**. Hechos con respaldo: 2 de 3 → **N3 = 1**.
Diagnóstico: **E1** (H4) + **E2** (H3 llegó y no se dijo) + **E3** (afirmación 1 sin respaldo). Primer eslabón: E1.
⚠ La afirmación 1 es el caso que el director pide afinar: es correcta pero el contexto no la sostiene; la respuesta la
presenta como si [1] la respaldara. Se evidencia sin necesidad de decir "incorrecta".

### LLM
| # | Afirmación | tipo | vs_ref | hecho | Códigos |
|---|---|---|---|---|---|
| 1 | APT29 no utiliza directamente Mimikatz | h | I | (contradice H1) | INC |
| 2 | La técnica de tickets Kerberos es "T1547.001 – Exploitation of Kerberos" | h | I | — | INC |
| 3 | Mimikatz extrae credenciales de memoria (incl. tickets) | h | F | — | — |
| — | OMISION H1, H2, H3, H4 | | | | OMI |

Verificado en `chunks.jsonl`: T1547.001 es *Registry Run Keys / Startup Folder*; "Exploitation of Kerberos" no existe en el corpus.
Derivado: C = 0 → **N2 = 0**, N3 = N/A. Diagnóstico: **E2**.

---
## p09 — Mitigaciones de Phishing + producto comercial (en, parcial)

**Hechos:** H1 M1031 · H2 M1021 · H3 M1017 · H4 M1049 · H5 M1054 (SPF/DKIM/DMARC) · H6 M1047 (seis mitigaciones de T1566).
**Parte no respondible:** producto comercial recomendado por MITRE.
**Contexto (RAG):** solo r5 trae mitigaciones: el texto de M1054 (SPF, DKIM, DMARC; la cabecera "M1054 Software Configuration" quedó
cortada por el chunking) y "M1047 Audit". **`llegó`:** H5 SI (sin su etiqueta) · H6 SI · H1–H4 NO.

### RAG
| # | Afirmación | tipo | vs_ref | hecho | respaldo | cita → sostiene | Códigos |
|---|---|---|---|---|---|---|---|
| 1 | Los pasajes no listan ninguna mitigación para T1566 | a | **I** | (niega H1–H6) | — | — | ABS-E |
| 2 | Los pasajes mencionan SPF, DKIM y DMARC para filtrado/validación | h | C | — ⚠ | S | [5] → r5 | — |
| 3 | No hay producto comercial recomendado | a | C | (parte no respondible) | — | — | — |
| — | OMISION H1–H6 (H5, H6 llegaron; H1–H4 no) | | | | | | OMI |

⚠ La afirmación 2 es verdadera pero no cuenta como cubrir H5, porque la respuesta niega que sean mitigaciones.
Derivado: C = 0 → **N2 = 0**. Un hecho con respaldo → **N3 = 2**. Diagnóstico: **E1** (H1–H4) + **E2** (H5 y H6 llegaron y se negaron).
La nota del piloto (N2 = 0) se conserva, pero el diagnóstico pasa de "E1" a "E1 + E2": la abstención errónea sobre lo que sí llegó
ya no queda oculta. La abstención sobre el producto comercial es correcta y no genera código.

### LLM
| # | Afirmación | tipo | vs_ref | hecho | Códigos |
|---|---|---|---|---|---|
| 1 | ATT&CK no lista mitigaciones específicas para T1566 | h | I | — | INC |
| 2 | Recomienda DMARC, SPF y DKIM | h | C | H5 | — |
| 3 | Recomienda educación/concienciación de usuarios | h | C | H3 | — |
| 4 | Recomienda filtrado de contenido, inteligencia de amenazas y análisis de comportamiento | h | F | — | — |
| 5 | MITRE no recomienda un producto comercial concreto | h | C | (parte no respondible) | — |
| 6 | Microsoft 365 Defender "es ampliamente referenciado en ATT&CK" como producto que implementa las mitigaciones | h | F | (parte no respondible) | NO-ABS |
| — | OMISION H1, H2, H4, H6 | | | | OMI |

Derivado: C = 2 de 6, con INC y NO-ABS → **N2 = 1**. Diagnóstico: **E0-no-abstencion + E2**. Nota: las afirmaciones 5 y 6 se
contradicen entre sí; no se resuelve en la tabla, se anota.

---
## p01 — Mitigaciones de T1059.001 (es, respondible completa)

**Hechos:** H1 M1038 Execution Prevention · H2 M1045 Code Signing · H3 M1026 Privileged Account Management · H4 M1049 Antivirus/Antimalware · H5 M1042 Disable or Remove Feature or Program.
**Contexto (RAG):** r1 T1059.001 (sin sus mitigaciones), r2–r3 software/grupo, r4 T1059 padre, r5 PowerStallion. Ningún gold (0/2).
`llegó`: H1–H4 NO · **H5 ALT-P** (r4, el padre T1059, trae "M1042 Disable or Remove Feature or Program" en versión genérica,
sin la parte de PowerShell/WinRM; verificado revisando los fragmentos, no solo el gold).

### RAG
| # | Afirmación | tipo | vs_ref | hecho | respaldo | Códigos |
|---|---|---|---|---|---|---|
| 1 | Los contextos no dan información sobre mitigaciones de T1059.001 | a | I | (niega H1–H5) | — | ABS-E |
| — | OMISION H1–H5 | | | | | OMI |

Derivado: C = 0 → **N2 = 0**; sin afirmaciones de hecho → **N3 = N/A**. Diagnóstico: **E1** (H1–H5; H5 solo llegó como evidencia parcial `ALT-P`).
⚠ Por defecto (§4.1) un fragmento `ALT-P` no cuenta como "llegó"; `evidence_check.py` marca H5 como ALT-P. Con ese criterio estricto
el diagnóstico queda solo **E1** (como en el piloto); se mostraría E1 + E2 solo si el evaluador acepta el texto genérico del padre
como evidencia.

### LLM  (respuesta truncada: `completion_tokens` = 1024 → `TRUNC`)
| # | Afirmación | tipo | vs_ref | hecho | Códigos |
|---|---|---|---|---|---|
| 1 | ATT&CK no proporciona una lista detallada de mitigaciones por sub-técnica | h | I | — | INC |
| 2 | Limitar PowerShell a modos "Restricted"/"RemoteSigned" | h | F | — | — |
| 3 | Requerir scripts firmados (ExecutionPolicy) | h | C | H2 | — |
| 4 | Monitoreo, auditoría y detección de comportamiento anómalo (Event ID 4688, SIEM) | h | F | — | — |
| 5 | Políticas de grupo para limitar el acceso a PowerShell a usuarios autorizados | h | C ⚠ | H3 | — |
| 6 | Usar alternativas (cmd, batch) en entornos críticos | h | F | — | — |
| — | OMISION H1, H4, H5 · `TRUNC` | | | | OMI |

⚠ La afirmación 5 cubre H3 de forma laxa (restringir quién ejecuta). Derivado: C = 2 de 5, con INC → **N2 = 1**. Diagnóstico: **E2**.
Las afirmaciones F se reportan aparte como "extras no incluidos en la referencia".

---
## p06 — Sub-técnicas de Lazarus + ataques contra Ecuador (es, parcial)

**Hechos:** H1 T1059.001 PowerShell · H2 T1059.003 Windows Command Shell · H3 T1059.005 Visual Basic. **No respondible:** ataques contra Ecuador.
**Contexto (RAG):** r1 AuditCred (T1059.003), r3 TYPEFRAME (T1059.003 y T1059.005), r5 G0032 con las tres. **`llegó`:** H1 SI (r5) · H2 SI · H3 SI.

### RAG
| # | Afirmación | tipo | vs_ref | hecho | respaldo | cita → sostiene | Códigos |
|---|---|---|---|---|---|---|---|
| 1 | Los contextos no dicen qué sub-técnicas T1059.* usa Lazarus | a | I | (niega H1–H3) | — | — | ABS-E |
| 2 | Lazarus usa T1059.003 y T1059.005 (vía AuditCred y TYPEFRAME) | h | C | H2, H3 | S | [1][3] → r1, r3 | — |
| 3 | No hay referencia a ataques contra Ecuador | a | C | (parte no respondible) | — | — | — |
| — | OMISION H1 (llegó, en r5) | | | | | | OMI |

Derivado: C = 2 de 3, con ABS-E → **N2 = 1**; un hecho con respaldo → **N3 = 2**. Diagnóstico: **E2**.
⚠ El piloto dio N2 = 0 porque la conclusión final es "no se puede determinar". Ver "Discrepancias".

### LLM
| # | Afirmación | tipo | vs_ref | hecho | Códigos |
|---|---|---|---|---|---|
| 1 | ATT&CK no documenta que Lazarus use sub-técnicas T1059.* | h | I | — | INC |
| 2 | No hay evidencia de ataques de Lazarus contra Ecuador | h | C | (parte no respondible) | — |
| — | OMISION H1–H3 | | | | OMI |

Derivado: C = 0 → **N2 = 0**; **E2**.

---
## Comparación con el piloto (v1.1)

| Caso | Modo | N2 piloto → v2 | N3 piloto → v2 | Diagnóstico piloto → v2 |
|---|---|---|---|---|
| p01 | RAG | 0 → 0 | N/A → N/A | E1 → E1 (E1 + E2 si se acepta ALT-P) |
| p01 | LLM | 1 → 1 | N/A → N/A | E2 → E2 |
| p05 | RAG | 1 → 1 | 1 → 1 | E1 → E1 + E2 + E3 |
| p05 | LLM | 0 → 0 | N/A → N/A | E2 → E2 |
| p06 | RAG | **0 → 1** | 2 → 2 | E2 → E2 |
| p06 | LLM | 0 → 0 | N/A → N/A | E2 → E2 |
| p09 | RAG | 0 → 0 | 2 → 2 | E1 → E1 + E2 |
| p09 | LLM | **0 → 1** | N/A → N/A | E2 → E0 + E2 |

Las notas coinciden en 6 de 8 respuestas; los diagnósticos se enriquecen. Las dos discrepancias de N2 fueron decisiones de regla,
no errores, y se resolvieron el 2026-10-12 con la decisión **"sin topes"** (§3.4 del protocolo): N2 queda descriptivo y los
problemas graves se señalan con alertas.

1. **p06 RAG (0 → 1).** La respuesta menciona correctamente dos de las tres sub-técnicas pero concluye "no se puede determinar".
   Con N2 sin topes da 1 (cubre 2 de 3 hechos) y se marca la alerta `CRITICA(ABS-E)`. El 0 del piloto reflejaba la conclusión final.
2. **p09 LLM (0 → 1).** Acierta 2 de 6 mitigaciones, pero inventa un producto comercial (`NO-ABS`). Con N2 sin topes da 1 y se marca
   `CRITICA(INC, NO-ABS)`; el diagnóstico incluye E0.

Hallazgos de método que surgieron al calificar (ya incorporados al protocolo, §3.2 y §4.1 de `protocol_v2.2.md`):
- Distinción entre **abstención** ("el contexto no dice…") y **afirmación de ausencia** ("ATT&CK no documenta…"): la segunda es `hecho` y puede ser `INCORRECTA`.
- En preguntas de lista cerrada, los elementos extra no están en la referencia → `FUERA_REF` (se reportan aparte), no `INC`.
- `llegó = ALT` hay que verificarlo leyendo los fragmentos recibidos, no solo `gold_points_found` (caso p01/H5, p05/H2–H3).
