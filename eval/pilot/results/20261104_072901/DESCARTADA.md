# Corrida descartada (2026-11-04)

Esta corrida (18 preguntas de `eval/run2/questions.jsonl`, 36 respuestas sin errores) se hizo con el contenedor `rag-api`
todavía sobre la **imagen del 2026-09-12**: `docker compose build ingest api` había construido la imagen nueva, pero
`docker compose up ingest` solo recreó el contenedor de ingesta; el de la API siguió con la imagen antigua (sin
`vectorstore.rank_hits`: desempate no determinista y fusión RRF sobre `top_k` candidatos en vez de `top_k × 4`).

Evidencia: `docker inspect rag-api` → imagen `e9ff28ba…` (creada 2026-09-12) frente a `rag-mitre-api:latest` = `3705a8d0…`
(2026-10-30). Tras recrear el contenedor (`docker compose up -d --force-recreate --no-deps api`), `--check-ties` devuelve el
mismo top-5 que la traza en 17/18 preguntas; en **n06** la API nueva trae además `G0096` chunk 5/5 (gold, sección
*Software used*, RRF 0,373) que la antigua no devolvía.

Incumple el criterio §8.6 del protocolo v2.3 (desempate determinista **antes** de la corrida), así que no se califica.
Se conserva como registro; la corrida válida es la siguiente carpeta con el mismo `questions.jsonl`.

Lección (añadida a CONTEXTO_PROYECTO.md): tras `docker compose build`, recrear **todos** los contenedores afectados
(`docker compose up -d --force-recreate api ingest`) y comprobar `docker inspect <contenedor> --format '{{.Image}}'`
contra `docker images`.
