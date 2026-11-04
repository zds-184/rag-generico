# Corrida 20261104_072901: réplica previa de la corrida 2 (no se califica)

Primera ejecución del conjunto `eval/run2/questions.jsonl` (18 preguntas, 36 respuestas, 0 errores). Se repitió como
`20261104_084930` por una sospecha que resultó infundada: el contenedor `rag-api` llevaba la imagen Docker del 2026-09-12,
pero la API monta `./app:/code` con `--reload`, así que **ya ejecutaba el código actual** (`vectorstore.rank_hits`). La
imagen solo fija las dependencias. (La ingesta, en cambio, no monta el código: por eso la primera reingesta del 2026-10-30 sí
usó el chunking viejo hasta reconstruir la imagen.)

Comparación entre las dos corridas (misma `questions.jsonl`, mismo corpus `bcd2ed8e…`, misma configuración):

| | 072901 | 084930 |
|---|---|---|
| Contextos recuperados (RAG, 18 preguntas) | idénticos en 18/18 | |
| Respuestas generadas iguales | 17/36 | |
| Respuestas distintas pese a `temperature=0` | 19/36 (longitudes distintas; mismo sentido en una lectura rápida) | |
| Errores / truncadas | 0 / 0 | 0 / 0 |

Conclusión: la recuperación es determinista (D6 verificado); la **generación no lo es** en Ollama/CPU aunque la temperatura
sea 0. Se califica la corrida `20261104_084930` (la que corrió con la imagen reconstruida, para que no quede duda de
trazabilidad) y esta se conserva como evidencia del no determinismo de la generación, que se añade a las limitaciones (§6).
