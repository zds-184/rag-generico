# Ejemplos calificados por afirmación — borrador para la reunión

**Estado: revisado contra la calificación manual (2026-10-22).** Las calificaciones de referencia son las de
`v2/calificacion_v2.xlsx`. Se corrigieron las afirmaciones de p06 y p09 en que el borrador (hecho por Claude) difería de esa
calificación. El evaluador 2 (`v2/calificacion_v2_eval_independent.xlsx`) discrepa en algunos de estos casos; se indica en
"Para discutir". Corrida `20260922_064359` (sin modificar). Modos: RAG y LLM.

Leyenda: `tipo` h = hecho, a = abstención · `vs_ref` C = CORRECTA, I = INCORRECTA, F = FUERA_REF ·
`respaldo` S = SOSTENIDA, X = CITA-X, SC = SIN-CITA, SR = SIN-RESPALDO · `llegó` SI / ALT / ALT-P / NO.

Casos elegidos: p05, p09, p01 y p06. Cubren los cuatro niveles: p05 (correcta sin respaldo, E3 y E1), p09 (abstención
errónea sobre lo que sí llegó, E2), p01 (recuperación fallida y truncamiento, E1 y E2) y p06 (abstención con evidencia
recuperada, E2).

---

## Caso 1 — p05: APT29 / Mimikatz (ES, respondible completa)

**Referencia:** H1 APT29 usa Mimikatz · H2 T1550.003 Pass the Ticket · H3 T1558.001 Golden Ticket · H4 T1558.002 Silver Ticket.
**Contexto recibido (RAG):** r1 y r2 sobre T1550.003 (por separado: "G0016 APT29: … tickets Kerberos" y "S0002 Mimikatz: `KERBEROS::PTT`"); r5 T1558.001 ("Mimikatz's kerberos module can create golden tickets").
**Llegó:** H1 NO (los dos nombres aparecen en la misma lista, sin vínculo) · H2 ALT (r1/r2) · H3 ALT (r5) · H4 NO.

### RAG

| # | Afirmación | tipo | vs_ref | hecho | respaldo | cita → sostiene | Códigos |
|---|---|---|---|---|---|---|---|
| 1 | APT29 (G0016) utiliza Mimikatz | h | C | H1 | SR ⚠ | [1] → ninguno | SIN-R |
| 2 | APT29 usó ataques Kerberos para movimiento lateral | h | F | — | S | [1] → r1 | — |
| 3 | Mimikatz implementa T1550.003 Pass the Ticket (KERBEROS::PTT) | h | C | H2 | S | [1] → r1 | — |
| — | OMISION H3 (Golden Ticket), llegó ALT | | | | | | OMI |
| — | OMISION H4 (Silver Ticket), llegó NO | | | | | | OMI |

**Derivado:** C = 2 de 4 → **N2 = 1**. Hechos con respaldo 2 de 3 → **N3 = 1**.
**Diagnóstico:** E1 (H4) + E2 (H3 llegó y no se dijo) + E3 (afirmación 1 sin respaldo). Primer eslabón: E1.

### LLM

| # | Afirmación | tipo | vs_ref | hecho | Códigos |
|---|---|---|---|---|---|
| 1 | APT29 no utiliza directamente Mimikatz | h | I (contradice H1) | — | INC |
| 2 | La técnica de tickets Kerberos es "T1547.001 – Exploitation of Kerberos" | h | I | — | INC |
| 3 | Mimikatz extrae credenciales de memoria (incl. tickets) | h | F | — | — |
| — | OMISION H1–H4 | | | | OMI |

**Derivado:** C = 0 → **N2 = 0**. **Diagnóstico:** E2. Verificado en `chunks.jsonl`: T1547.001 es *Registry Run Keys / Startup
Folder*, y "Exploitation of Kerberos" no existe en el corpus.

**Para discutir:**
- ⚠ RAG afirmación 1: es correcta según la referencia, pero el fragmento no la sostiene. ¿Se cuenta como `SIN-RESPALDO`
  aunque la referencia la avale? Así lo define §4.2 (dos nombres en la misma lista no sostienen "A usa B"). Coincide con el
  evaluador 2.
- RAG afirmación 2 (ataques Kerberos para movimiento lateral): la calificación manual la marca `SOSTENIDA` con [1]; el
  evaluador 2 la marca `CITA-X`. Hay que decidir si r1 (G0016 "usó ataques de tickets Kerberos") basta para sostenerla.
- ¿Es E1 el primer eslabón o E2? H3 llegó como ALT, así que la omisión de H3 es de generación; H4 no llegó y sí es de recuperación.

---

## Caso 2 — p09: Mitigaciones de Phishing + producto comercial (EN, parcial)

**Referencia:** H1 M1031 · H2 M1021 · H3 M1017 · H4 M1049 · H5 M1054 (SPF/DKIM/DMARC) · H6 M1047 (mitigaciones de T1566).
**No respondible:** producto comercial recomendado por MITRE.
**Contexto (RAG):** solo r5 trae mitigaciones (texto de M1054 con la cabecera cortada por el chunking, y M1047).
**Llegó:** H5 SI (sin su etiqueta) · H6 SI · H1–H4 NO.

### RAG

| # | Afirmación | tipo | vs_ref | hecho | respaldo | cita → sostiene | Códigos |
|---|---|---|---|---|---|---|---|
| 1 | Los pasajes no listan ninguna mitigación para T1566 | a | I (niega H1–H6) | — | — | — | ABS-E |
| 2 | Los pasajes mencionan SPF, DKIM y DMARC para filtrado/validación | h | C ⚠ | — | S | [5] → r5 | — |
| 3 | No hay producto comercial recomendado | a | FUERA_REF (parte no respondible) | — | — | — | — |
| — | OMISION H1, H2, H3, H4, H6 (H5 llegó; H6 llegó y no se cubrió) | | | | | | OMI |

**Derivado:** C = 1 (H5, por la afirmación 2) → **N2 = 1**. Hechos con respaldo 2 de 2 → **N3 = 2**. Alerta `CRITICA` (ABS-E).
**Diagnóstico:** E1 (H1–H4 no llegaron) + E2 (H5 y H6 llegaron y la afirmación 1 los niega). El piloto dio N2 = 0; la
calificación manual da 1 porque la afirmación 2 cubre H5 con cita sostenida.

### LLM

| # | Afirmación | tipo | vs_ref | hecho | Códigos |
|---|---|---|---|---|---|
| 1 | ATT&CK no lista mitigaciones específicas para T1566 | h | I | — | INC |
| 2 | Recomienda DMARC, SPF y DKIM | h | C | H5 | — |
| 3 | Recomienda educación/concienciación de usuarios | h | C | H3 | — |
| 4 | Recomienda filtrado de contenido, inteligencia de amenazas y análisis de comportamiento | h | F | — | — |
| 5 | MITRE no recomienda un producto comercial concreto | h | FUERA_REF (parte no respondible) | — | NO-ABS |
| 6 | Microsoft 365 Defender "es ampliamente referenciado en ATT&CK" como producto que implementa las mitigaciones | h | F | — | NO-ABS |
| — | OMISION H1, H2, H4, H6 | | | | OMI |

**Derivado:** C = 2 de 6, con INC y NO-ABS → **N2 = 1**. **Diagnóstico:** E0-no-abstención + E2.
Las afirmaciones 5 y 6 se contradicen entre sí; se anota, no se resuelve en la tabla.

**Para discutir:**
- La afirmación 2 del RAG cubre H5 en la calificación manual, pero la misma respuesta niega las mitigaciones en la
  afirmación 1. El evaluador 2 no le asignó H5 (N2 = 0). ¿Cuenta la cobertura de H5 aunque la respuesta lo niegue? En ambos
  casos lo tratamos como E2.
- La abstención sobre el producto comercial es parte no respondible. La calificación manual la marca `FUERA_REF`; el
  evaluador 2 la marca `CORRECTA`. Ver la regla de "afirmaciones de ausencia" en la sección de discusión general.

---

## Caso 3 — p01: Mitigaciones de T1059.001 (ES, respondible completa)

**Referencia:** H1 M1038 Execution Prevention · H2 M1045 Code Signing · H3 M1026 Privileged Account Management ·
H4 M1049 Antivirus · H5 M1042 Disable or Remove Feature.
**Contexto (RAG):** r1 T1059.001 (sin sus mitigaciones), r2–r3 software/grupo, r4 T1059 padre, r5 PowerStallion. Ningún gold (0/2).
**Llegó:** H1–H4 NO · H5 ALT-P (r4: "M1042" en versión genérica del padre T1059, sin la parte de PowerShell/WinRM).

### RAG

| # | Afirmación | tipo | vs_ref | hecho | Códigos |
|---|---|---|---|---|---|
| 1 | Los contextos no dan información sobre mitigaciones de T1059.001 | a | I (niega H1–H5) | — | ABS-E |
| — | OMISION H1–H5 | | | | OMI |

**Derivado:** C = 0 → **N2 = 0**; sin afirmaciones de hecho → **N3 = N/A**.
**Diagnóstico:** E1 (H1–H5). Con el criterio estricto de §4.1 (ALT-P no cuenta como "llegó") queda solo E1; E1 + E2 solo si el
evaluador acepta el texto genérico del padre como evidencia.

### LLM (respuesta truncada: `completion_tokens` = 1024, `TRUNC`)

| # | Afirmación | tipo | vs_ref | hecho | Códigos |
|---|---|---|---|---|---|
| 1 | ATT&CK no proporciona una lista detallada de mitigaciones por sub-técnica | h | I | — | INC |
| 2 | Limitar PowerShell a modos "Restricted"/"RemoteSigned" | h | F | — | — |
| 3 | Requerir scripts firmados (ExecutionPolicy) | h | C | H2 | — |
| 4 | Monitoreo, auditoría y detección (Event ID 4688, SIEM) | h | F | — | — |
| 5 | Políticas de grupo para limitar el acceso a PowerShell a usuarios autorizados | h | C ⚠ | H3 | — |
| 6 | Usar alternativas (cmd, batch) en entornos críticos | h | F | — | — |
| — | OMISION H1, H4, H5 · TRUNC | | | | OMI |

**Derivado:** C = 2 de 5, con INC → **N2 = 1**. **Diagnóstico:** E2 (+ indicador TRUNC).

**Para discutir:**
- ⚠ Afirmación 5 contada como H3: cubre la restricción de acceso de forma laxa. ¿Cuenta como CORRECTA o como FUERA_REF?
- ALT-P en H5: ¿E1 o E1 + E2? Es la decisión de regla que más cambia el diagnóstico de este caso.

---

## Caso 4 — p06: Sub-técnicas de Lazarus + ataques contra Ecuador (ES, parcial)

**Referencia:** H1 T1059.001 PowerShell · H2 T1059.003 Windows Command Shell · H3 T1059.005 Visual Basic.
**No respondible:** ataques contra Ecuador.
**Contexto (RAG):** r1 AuditCred (T1059.003), r3 TYPEFRAME (T1059.003 y T1059.005), r5 G0032 con las tres.
**Llegó:** H1 SI (r5) · H2 SI · H3 SI.

### RAG

| # | Afirmación | tipo | vs_ref | hecho | respaldo | cita → sostiene | Códigos |
|---|---|---|---|---|---|---|---|
| 1 | Los contextos no dicen qué sub-técnicas T1059.* usa Lazarus | a | I (niega H1–H3) | — | — | — | ABS-E |
| 2 | Lazarus usa T1059.003 y T1059.005 (vía AuditCred y TYPEFRAME) | h | C | H2, H3 | S | [1][3] → r1, r3 | — |
| 3 | No hay referencia a ataques contra Ecuador | a | FUERA_REF (parte no respondible) | — | — | — | — |
| — | OMISION H1 (llegó, en r5) | | | | | | OMI |

**Derivado:** C = 2 de 3, con ABS-E → **N2 = 1**; un hecho con respaldo → **N3 = 2**. **Diagnóstico:** E2.

### LLM

| # | Afirmación | tipo | vs_ref | hecho | Códigos |
|---|---|---|---|---|---|
| 1 | ATT&CK no documenta que Lazarus use sub-técnicas T1059.* | h | I | — | INC |
| 2 | No hay evidencia de ataques de Lazarus contra Ecuador | h | FUERA_REF (parte no respondible) | — | NO-ABS |
| — | OMISION H1–H3 | | | | OMI |

**Derivado:** C = 0 → **N2 = 0**. **Diagnóstico:** E0-no-abstención + E2. Primer eslabón: E0 (responde a la parte no
respondible y además omite H1–H3, que llegaron).

**Para discutir:**
- El piloto dio N2 = 0 al RAG porque la conclusión final es "no se puede determinar". Con N2 sin topes da 1 y se marca
  `CRITICA(ABS-E)`. ¿Es la nota correcta, o el veredicto final debe pesar más?
- Aquí la abstención es el problema: los tres hechos llegaron y el modelo se abstuvo. Muestra por qué separamos cobertura
  de veredicto.
- Afirmaciones de ausencia sobre la parte no respondible ("No hay referencia a ataques contra Ecuador", "No hay evidencia
  de ataques…"). La calificación manual las marca `FUERA_REF` (y `NO-ABS` en el LLM); el evaluador 2 las marca `CORRECTA`.
  Es la regla que más afecta a estos casos.
- LLM afirmación 1 ("ATT&CK no documenta que Lazarus use sub-técnicas"): la calificación manual la marca `hecho` e
  `INCORRECTA`; el evaluador 2 la marca `abstención`. Ver la distinción abstención vs. afirmación de ausencia (§3.2).

---

## Resumen para la reunión

| Caso | RAG (N2 / N3) | LLM (N2) | Qué muestra |
|---|---|---|---|
| p05 | 1 / 1 | 0 | Afirmación correcta sin respaldo (E3); omisión de evidencia alternativa (E2); E1 |
| p09 | 1 / 2 | 1 | Abstención errónea sobre lo que sí llegó (E2); el LLM inventa un producto (NO-ABS) |
| p01 | 0 / N/A | 1 | Recuperación fallida (E1); truncamiento y regla de ALT-P |
| p06 | 1 / 2 | 0 | Abstención con evidencia recuperada (E2); la nota del piloto cambia con la regla "sin topes" |

