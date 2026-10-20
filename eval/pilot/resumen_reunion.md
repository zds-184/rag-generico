# Resumen para la reunión: protocolo v2 del piloto

**Enfoque:** evaluar y diagnosticar respuestas de un RAG sobre MITRE ATT&CK (qwen3:4b, 13 preguntas × 2 modos). No se optimiza el RAG. El piloto original queda intacto; todo lo nuevo es aparte (`protocol_v2.md`).

## Qué cambió respecto a lo pedido

| Punto | Cambio |
|---|---|
| 1. Qué se califica | Tabla **por afirmación**: tipo (hecho o abstención), corrección frente a la referencia y respaldo en los fragmentos recibidos. Se distinguen incorrecta, incompleta (omisión) y correcta sin respaldo. Una respuesta puede tener varios problemas. N2 y N3 (0/1/2) se **derivan** de la tabla. Diagnóstico como lista de causas (E0–E3). |
| 2. Recuperación y citas | N1 por **evidencia**, no por fragmento gold: ninguna, parte o toda, aceptando fragmentos alternativos. Reglas de citas: la cita debe expresar la relación, no solo nombrar las entidades; se revisan también en respuestas incorrectas. |
| 3. Con y sin RAG | La diferencia de N2 deja de ser el titular. Se reportan por separado: fidelidad a la referencia, abstención, respaldo documental (solo RAG) y contenido fuera de la referencia. |
| 4. Matriz | Se añadieron ALCE y CiteEval (leídos en sus PDF). La diferenciación pasa de "las citas no se han estudiado" a **diagnóstico encadenado** (corpus → recuperación → generación → citas), con referencia por hechos y abstención. |

Decisión de diseño: N2 y N3 **sin topes**; los problemas graves se señalan con alertas (`CRITICA`, `RESPALDO`, `TRUNC`) y la política es configurable, pensando en el módulo de auditoría continua.

## Ejemplos calificados por afirmación (RAG)

| Caso | Hallazgo | N2 | Diagnóstico |
|---|---|---|---|
| p05 APT29/Mimikatz | "APT29 usa Mimikatz" es correcta pero ningún fragmento la sostiene; falta Golden Ticket (llegó) y Silver Ticket (no llegó) | 1 | E1 + E2 + E3 |
| p09 mitigaciones de Phishing | Niega las mitigaciones aunque el fragmento 5 las traía; la abstención sobre el producto comercial es correcta | 0 | E1 + E2 |
| p01 PowerShell | La recuperación no trajo las mitigaciones; el modo LLM es truncado e incluye una afirmación falsa | 0 (RAG), 1 (LLM) | E1 / E2 |
| p06 Lazarus | El gold llegó pero se abstuvo; menciona bien 2 de 3 sub-técnicas | 1 | E2 |

**Lo que muestra:** con las 8 respuestas calificadas, la cobertura total de hechos es **4/18 en ambos modos**, pero distribuida distinto (p05 y p06 favorecen al RAG; p01 y p09, al LLM, este con afirmaciones incorrectas y un producto comercial inventado). Una nota única esconde esa estructura. En p02 y p09 el gold llegó pero solo 1/5 y 2/6 hechos; en p05 no llegó ningún gold pero sí evidencia alternativa para 2 de 4 hechos.

## Límites que declaro

- p06 (RAG) y p09 (LLM) dan N2 = 1 y el piloto les puso 0: es consecuencia de separar cobertura y veredicto, no un error.

## Preguntas 

1. **Segundo evaluador.** se define evaluacion de 4 preguntas representativas p01, p05, p06, p09

## Pendiente

Corrida reproducible (corregir el solape del chunking, verificar la ingesta, proteger las calificaciones, congelar la versión del corpus y los límites de generación), conjunto nuevo de preguntas equilibrado por cobertura del corpus, y propuesta de evaluación final.
