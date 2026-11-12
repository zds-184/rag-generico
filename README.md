# RAG genérico local sobre MITRE ATT&CK

Arquitectura RAG **deliberadamente genérica** (chunking por caracteres → embeddings + BM25 → búsqueda top‑k híbrida/densa/léxica → prompt con contexto → LLM), 100 % local con Docker Compose, pensada para servir como *sistema bajo prueba* de un evaluador de RAG.

| Componente | Tecnología | Puerto |
|---|---|---|
| LLM + embeddings | [Ollama](https://ollama.com) (`qwen3:4b-instruct` por defecto, `granite-embedding:30m`) | 11434 |
| Base vectorial | [Qdrant](https://qdrant.tech) | 6333 (REST/dashboard), 6334 (gRPC) |
| API | FastAPI (`/query`, `/retrieve`, `/models`, `/collection`, `/health`) | 8000 |
| Interfaz web | Streamlit, selector **RAG / Solo LLM / Comparar ambos** | 8501 |
| Corpus | MITRE ATT&CK STIX 2.1 desde `mitre-attack/attack-stix-data` (descarga la rama `master`; los resultados publicados usan **Enterprise v19.2**, ver más abajo) | — |

## Evaluación de este sistema

Este RAG es el *sistema bajo prueba* de un trabajo de titulación (Maestría en Ciencia de Datos, USFQ) sobre **evaluación diagnóstica**. No se optimiza el RAG. Se califica cada **afirmación** de cada respuesta y se localiza en qué eslabón se pierde cada hecho de la referencia: corpus (N0) → recuperación (N1) → generación (N2) → citas (N3). El mismo modelo se evalúa con recuperación (`rag`) y sin ella (`llm`).

**Empieza por [`eval/pilot/protocol_v2.3.md`](eval/pilot/protocol_v2.3.md)**, la **rúbrica congelada** con las decisiones del director D1–D12 (2026-10-29 y 2026-11-10). El cierre de la evaluación está en [`eval/pilot/propuesta_evaluacion_final.md`](eval/pilot/propuesta_evaluacion_final.md).

### Resumen de resultados

| | Piloto | Corrida 2 |
|---|---|---|
| Corrida (`eval/pilot/results/`) | `20260922_064359` | `20261104_102233` |
| Preguntas (completa / parcial / nula) | 13 (5/4/4) | 18 (6/6/6) |
| Respuestas calificadas (RAG + LLM) / afirmaciones | 26 / 92 | 36 / 142 |
| Hechos de referencia cubiertos, RAG vs LLM | 14/33 vs 7/33 | 27/42 vs 7/42 |
| Respuestas sin base (`NO-ABS`), RAG vs LLM | 0 vs 7 | 0 vs 8 |
| Abstenciones erróneas (`ABS-E`) del RAG | 3 | 4 |

Consistencia (RQ6): un segundo evaluador independiente calificó 27 afirmaciones de cuatro preguntas del piloto. El acuerdo en `vs_ref` fue de 22/27 (**κ de Cohen 0,73**). Tras fijar las reglas que esos desacuerdos obligaron a escribir, la adjudicación llega a 26/27, pero se reporta aparte (decisión D12). Todos los resultados son descriptivos: un sistema, una configuración y una muestra pequeña.

### Mapa de archivos

| Qué | Dónde |
|---|---|
| Protocolo vigente (v2.3) y su resumen de decisiones | `eval/pilot/protocol_v2.3.md`, `eval/pilot/protocol_v2.3_estructura.md` |
| Versiones anteriores, solo como historial | `eval/pilot/protocol.md` (v1.1), `protocol_v2.md`, `protocol_v2.2.md` |
| Script de corrida, controles previos y pruebas | `eval/pilot/run_pilot.py`, `eval/pilot/check_ingest.py`, `eval/pilot/tests/` |
| **Piloto**: preguntas, traza y calificación v2.3 | `eval/pilot/questions.jsonl`, `eval/pilot/results/20260922_064359/`, `eval/pilot/v2/calificacion_v2.xlsx` |
| Piloto: segundo evaluador (RQ6) | `eval/pilot/v2/calificacion_v2_eval_independent.xlsx` |
| **Corrida 2**: preguntas y diseño del conjunto | `eval/run2/questions.jsonl`, `eval/run2/propuesta_preguntas.md`, `eval/run2/validacion_referencias.xlsx` |
| Corrida 2: traza válida | `eval/pilot/results/20261104_102233/` (traces, config, huella del corpus, gold, empates) |
| Corrida 2: calificación final | `eval/run2/calificacion_v2_run2.xlsx` |
| Corrida 2: revisión asistida (D11) | `eval/run2/calificacion_v2_run2_revisada.xlsx` (hoja `Revisión`: antes, después, motivo, `¿aceptas?`) y `calificacion_v2_run2_original_reconstruida.xlsx` (calificación previa a la revisión) |
| Corrida 2: extracción asistida de afirmaciones (sin juicio) | `eval/run2/afirmaciones_extraidas.json`, `fill_afirmaciones.py`, `fill_gold.py` |
| Réplicas que **no se califican** | `results/20261104_072901/` y `results/20261104_084930/` (ver su `REPLICA.md`); muestran que con contextos idénticos cambian 19 de 36 respuestas pese a `temperature=0` |
| Herramientas de la rúbrica v2 y datos de apoyo | `evidence_build.py`, `evidence_check.py`, `comparar_modos.py`, `build_calificacion_v2.py`, `evidence_pilot.json`, `afirmaciones_ejemplos.csv` |
| Plantillas Excel | `eval/pilot/v2/calificacion_v2_DEMO.xlsx` (8 respuestas de ejemplo), `calificacion_v2_piloto.xlsx` (en blanco) |

### Reproducir

Las herramientas de calificación no requieren Ollama ni Qdrant:

```bash
python eval/pilot/evidence_check.py eval/pilot/results/20260922_064359
python eval/pilot/comparar_modos.py eval/pilot/afirmaciones_ejemplos.csv
python eval/pilot/tests/test_chunking.py
python eval/pilot/tests/test_rank_hits.py
python eval/pilot/tests/test_run_pilot_guards.py
```

Una corrida nueva requiere el sistema levantado con la ingesta completa y tarda ~35 min en CPU:

```bash
python eval/pilot/check_ingest.py
python eval/pilot/run_pilot.py --questions eval/run2/questions.jsonl
python eval/pilot/run_pilot.py --check-ties eval/pilot/results/<corrida>
```

`run_pilot.py` usa la configuración de las corridas publicadas (`hybrid`, `top_k=5`, `temperature=0`, modos `rag,llm`) y guarda con cada corrida `config.json`, la huella SHA-256 de `chunks.jsonl`, una instantánea de las preguntas y el texto de los fragmentos gold. Por seguridad:
- se niega a arrancar si la ingesta está incompleta;
- con `--resume`, se niega a continuar si la configuración cambió;
- con `--rebuild-xlsx`, no sobrescribe un libro ya calificado salvo con `--force`.

**Versión del corpus.** La ingesta descarga la última versión publicada. Para reproducir los resultados hay que usar **Enterprise v19.2**: 2 616 documentos y 7 244 chunks, `chunks_jsonl_sha256` registrado en el `config.json` de cada corrida. Si `master` ya avanzó, apunta `ATTACK_BASE_URL` en `.env` al commit o tag de `attack-stix-data` que publica v19.2 y reingesta con `FORCE_REINGEST=true`.

## Arquitectura

```
                           ┌──────────────────────────────────────────────────────────────┐
                           │                       docker compose                         │
                           │                                                              │
   GitHub                  │  ┌────────────┐   STIX 2.1    ┌──────────────┐               │
   attack-stix-data ───────┼─▶│  ingest    │──────────────▶│  documentos  │               │
   (enterprise/mobile/ics) │  │ (one-shot) │  parse+enrich │  markdown    │               │
                           │  └────────────┘               └──────┬───────┘               │
                           │                                      │ chunking               │
                           │                                      ▼                        │
                           │                      ┌──────────┐ embed ┌───────────┐         │
                           │                      │  Ollama  │◀──────│  chunks   │         │
                           │                      │ (embed)  │──────▶│ + payload │──┐      │
                           │                      └──────────┘       └───────────┘  │upsert│
                           │                                                        ▼      │
   Navegador ──▶ :8501 ──▶ ┌────────────┐  POST /query  ┌───────────┐   search   ┌────────┐│
                           │  UI        │──────────────▶│   API     │───────────▶│ Qdrant ││
   Evaluador ──▶ :8000 ──▶ │ Streamlit  │◀──────────────│  FastAPI  │◀───────────│        ││
                           └────────────┘  answer +     └─────┬─────┘  top-k     └────────┘│
                           │              contexts +          │ chat                       │
                           │              prompt + timings    ▼                             │
                           │                            ┌──────────┐                        │
                           │                            │  Ollama  │  qwen3:4b-instruct/otro│
                           │                            │  (LLM)   │                        │
                           │                            └──────────┘                        │
                           └──────────────────────────────────────────────────────────────┘

   modo "rag":  pregunta ─▶ embed ─▶ top-k Qdrant ─▶ prompt(context+pregunta) ─▶ LLM
   modo "llm":  pregunta ─────────────────────────▶ prompt(pregunta) ─────────▶ LLM
```

## Requisitos

- Docker Desktop (Windows 11 con backend WSL2 recomendado) con ≥ 8 GB de RAM asignados.
- ~6 GB de disco: `qwen3:4b-instruct` (~2.5 GB) + `qwen3:4b` (~2.5 GB, opcional) + `granite-embedding:30m` (~60 MB) + STIX (~50 MB) + índice.
- Opcional: GPU NVIDIA + NVIDIA Container Toolkit para acelerar Ollama. **Sin GPU todo funciona, pero lento**: en un portátil de 4 núcleos (i5/i7 11ª gen) medimos ~5 tok/s de generación y ~19 tok/s de lectura de prompt con qwen3:4b, es decir, 2‑4 min por respuesta RAG y ~40 min de ingesta inicial.

## Puesta en marcha

```bash
cd D:/DS_USFQ/CAPSTON/RAG
cp .env.example .env          # configuración local (el repositorio solo versiona .env.example)
docker compose up -d --build
```

Con GPU NVIDIA:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
```

Orden de arranque automático: `qdrant` + `ollama` → `ollama-init` (descarga modelos) → `ingest` (descarga ATT&CK, chunking, embeddings, upsert) → `api` y `ui` (ya disponibles desde el inicio; la UI muestra "degradado" hasta que la ingesta termina).

Seguir la ingesta:

```bash
docker compose logs -f ollama-init ingest
```

Tiempo estimado de la primera ingesta (enterprise-attack v19.2: ~2.600 documentos, ~7.200 chunks, ~5,9 M caracteres ≈ 2 M tokens) con `granite-embedding:30m`: 2‑5 min en GPU; en CPU de portátil (4 núcleos) medimos ~500 tok/s dentro de Docker, es decir, **60‑70 min**. Con `nomic-embed-text` (137 M parámetros) tarda ~2x más. Las siguientes veces se omite porque la colección ya existe. Para acelerar: `ATTACK_DOMAINS` sólo enterprise (ya por defecto), reducir `MAX_PROCEDURE_EXAMPLES`, o usar GPU.

Accesos:

- Interfaz web: <http://localhost:8501>
- Swagger de la API: <http://localhost:8000/docs>
- Dashboard de Qdrant: <http://localhost:6333/dashboard>

## Configuración (`.env`)

| Variable | Descripción | Por defecto |
|---|---|---|
| `LLM_MODEL` | Modelo generador en Ollama | `qwen3:4b-instruct` |
| `EXTRA_MODELS` | Modelos adicionales a descargar para poder alternarlos en la UI | `qwen3:4b` |
| `EMBED_MODEL` | Modelo de embeddings (cambiarlo exige `FORCE_REINGEST=true`) | `granite-embedding:30m` |
| `LLM_THINK` | Modo razonamiento para qwen3 / deepseek‑r1 (`false` = respuestas directas) | `false` |
| `LLM_TEMPERATURE`, `LLM_NUM_CTX`, `LLM_NUM_PREDICT` | Parámetros de generación (las corridas de evaluación fijan `temperature=0` por petición) | `0.1`, `4096`, `1024` |
| `REQUEST_TIMEOUT` | Timeout (s) de las llamadas a Ollama | `1800` |
| `ATTACK_DOMAINS` | `enterprise-attack`, `mobile-attack`, `ics-attack` (separados por coma) | `enterprise-attack` |
| `MAX_PROCEDURE_EXAMPLES` | Nº máx. de ejemplos de procedimiento por técnica | `25` |
| `CHUNK_SIZE`, `CHUNK_OVERLAP` | Chunking por caracteres | `1200`, `150` |
| `TOP_K` | Contextos recuperados por defecto | `5` |
| `RETRIEVAL_MODE` | `hybrid` (densa + BM25 fusionadas con RRF), `dense` o `sparse`; también se elige por petición | `hybrid` |
| `FORCE_REINGEST` | Reconstruir la colección | `false` |
| `REFRESH_CORPUS` | Volver a descargar el STIX | `false` |

### Modelos LLM alternativos

Cualquier modelo de la [biblioteca de Ollama](https://ollama.com/library) funciona. Opciones probadas para equipos con 8‑16 GB de RAM:

| Modelo | Tamaño | Notas |
|---|---|---|
| `qwen3:4b-instruct` | 2.5 GB | **Por defecto.** Qwen3‑4B‑Instruct‑2507, sin razonamiento: respuestas directas y rápidas. |
| `qwen3:4b` | 2.5 GB | Qwen3‑4B *thinking*. Se descarga también (`EXTRA_MODELS`). Úsalo con `LLM_THINK=true`; con `think=false` tiende a filtrar el razonamiento en la respuesta. |
| `qwen3:1.7b` | 1.4 GB | ~2x más rápido en CPU si el 4b resulta lento. |
| `llama3.2:3b` | 2.0 GB | Ligero, buen seguimiento de instrucciones. |
| `gemma3:4b` | 3.3 GB | Rápido, multilingüe. |
| `phi4-mini` | 2.5 GB | Muy ligero. |
| `llama3.1:8b` | 4.9 GB | Muy estable citando fuentes; lento en CPU. |
| `qwen3:8b` | 5.2 GB | Mejor calidad, lento en CPU. |
| `deepseek-r1:8b` | 5.2 GB | Razonador (activar `LLM_THINK=true` si se quiere ver el razonamiento). |

Tres formas de cambiar de modelo:

1. `.env` → `LLM_MODEL=llama3.1:8b` y `docker compose up -d` (lo descarga `ollama-init`).
2. `.env` → `EXTRA_MODELS=llama3.1:8b gemma3:4b` para tenerlos todos y elegir en la UI.
3. Desde la UI, "Descargar otro modelo", o `POST /models/pull {"model": "gemma3:4b"}`.

Embeddings alternativos: `nomic-embed-text` (768d, mejor calidad, ~5x más lento), `all-minilm`, `snowflake-arctic-embed:xs`, `mxbai-embed-large`, `bge-m3` (multilingüe, recomendado si las preguntas serán en español y hay GPU). Tras cambiarlo: `FORCE_REINGEST=true` y `docker compose up -d ingest`.

## API para el evaluador

`POST /query`

```json
{
  "question": "What is T1059.001 and which mitigations apply to it?",
  "mode": "rag",                 // "rag" | "llm"
  "top_k": 5,
  "model": "qwen3:4b-instruct",  // opcional, cualquier modelo cargado en Ollama
  "temperature": 0,
  "filters": {"object_type": ["technique", "sub-technique"]},   // opcional
  "think": false,
  "retrieval": "hybrid",         // "hybrid" | "dense" | "sparse" (opcional; por defecto RETRIEVAL_MODE)
  "include_prompt": true
}
```

Respuesta (todo lo necesario para métricas de retrieval y generación):

```json
{
  "question": "...", "mode": "rag", "model": "qwen3:4b-instruct",
  "answer": "...",
  "contexts": [
    {"rank": 1, "score": 0.0325, "point_id": "...", "text": "...",
     "metadata": {"attack_id": "T1059.001", "name": "PowerShell", "object_type": "sub-technique",
                  "domain": "enterprise-attack", "attack_version": "19.2", "url": "https://attack.mitre.org/techniques/T1059/001",
                  "tactics": ["execution"], "platforms": ["Windows"], "chunk_index": 0, "n_chunks": 3}}
  ],
  "prompt": {"system": "...", "user": "..."},
  "usage": {"prompt_tokens": 1834, "completion_tokens": 212},
  "timings_ms": {"retrieval": 41.2, "generation": 5321.0, "total": 5362.2, "ollama": {...}},
  "params": {"top_k": 5, "temperature": 0, "think": false, "embed_model": "granite-embedding:30m", "collection": "mitre_attack", "filters": {}}
}
```

Otros endpoints: `POST /query/batch` (lista de consultas), `POST /retrieve` (sólo contextos, para hit@k / MRR / nDCG), `GET /collection` (info + `manifest.json` de la ingesta), `GET /health`, `GET /models`.

Ejemplo de cliente evaluador: [`eval/example_client.py`](eval/example_client.py) recorre [`eval/sample_questions.jsonl`](eval/sample_questions.jsonl) en ambos modos, guarda los resultados en `eval/results/` y calcula un `hit@k` básico contra `expected_ids`.

```bash
pip install requests
python eval/example_client.py --api http://localhost:8000 --modes rag,llm --top-k 5
```

### Artefactos exportados por la ingesta (`./data`)

- `corpus/<dominio>.json` — STIX original descargado.
- `documents.jsonl` — un documento por objeto ATT&CK (técnica, sub‑técnica, grupo, software, mitigación, táctica, campaña, estrategia de detección con sus analíticas, data component) enriquecido con sus relaciones (procedure examples, mitigaciones, detecciones, sub‑técnicas...). Compatible con bundles anteriores a v18 (data sources y `x_mitre_detection`) y posteriores (detection strategies / analytics).
- `chunks.jsonl` — exactamente los chunks indexados en Qdrant, con su `id` y payload. Útil para generar preguntas sintéticas con *ground truth* de chunk.
- `manifest.json` — versión de ATT&CK, modelo/dimensión de embeddings, parámetros de chunking, conteos y duración.

## Estructura

```
RAG/
├─ docker-compose.yml        # servicios: qdrant, ollama, ollama-init, ingest, api, ui
├─ docker-compose.gpu.yml    # override GPU NVIDIA
├─ .env                      # toda la configuración
├─ app/                      # imagen Python compartida por api e ingest
│  ├─ main.py                # FastAPI
│  └─ rag/
│     ├─ config.py           # Settings desde .env
│     ├─ corpus_mitre.py     # descarga + STIX 2.1 -> documentos markdown enriquecidos
│     ├─ chunking.py         # split por caracteres respetando párrafos/oraciones
│     ├─ embeddings.py       # Ollama /api/embed con batching y prefijos
│     ├─ sparse.py           # vectores BM25 (tokenizador Unicode, IDs compuestos) para búsqueda léxica
│     ├─ vectorstore.py      # Qdrant: vectores "dense" + "bm25", búsqueda dense/sparse/hybrid (RRF), filtros
│     ├─ ollama_client.py    # /api/chat, /api/embed, /api/tags, /api/pull
│     ├─ prompts.py          # prompts RAG y LLM-only (misma persona, distinto grounding)
│     ├─ pipeline.py         # retrieve -> prompt -> generate
│     └─ ingest.py           # python -m rag.ingest
├─ ui/app.py                 # Streamlit
├─ eval/
│  ├─ example_client.py      # cliente de ejemplo + sample_questions.jsonl
│  ├─ pilot/                 # protocolo v2.3, run_pilot.py, check_ingest.py, tests/, piloto y results/ de todas las corridas
│  └─ run2/                  # conjunto de la corrida 2, extracción asistida y libros de calificación
└─ data/                     # artefactos de la ingesta (volumen)
```

## Operación

```bash
docker compose ps                              # estado
docker compose logs -f api                     # logs de la API
docker compose run --rm ingest                 # relanzar la ingesta manualmente
docker compose down                            # parar (conserva modelos e índice en volúmenes)
docker compose down -v                         # parar y borrar modelos + índice
```

Para usar un Ollama ya instalado en Windows en lugar del contenedor: en `.env` pon `OLLAMA_URL=http://host.docker.internal:11434`, descarga los modelos con `ollama pull qwen3:4b-instruct` y `ollama pull granite-embedding:30m` en el host, y arranca sin los servicios de Ollama: `docker compose up -d qdrant api ui` seguido de `docker compose run --rm --no-deps ingest`.

## Notas de diseño para la evaluación

- Los dos modos comparten *persona*, modelo, temperatura y parámetros; sólo difiere el grounding del prompt. Así la diferencia RAG vs LLM se atribuye al contexto recuperado.
- Cada respuesta devuelve el prompt exacto, los chunks con `score` y metadatos, tokens y tiempos: suficiente para faithfulness, answer relevancy, context precision/recall y coste/latencia.
- El retrieval ofrece tres estrategias seleccionables por petición: `dense` (coseno sobre embeddings), `sparse` (BM25: TF en cliente, IDF en Qdrant) e `hybrid` (ambas + Reciprocal Rank Fusion). La densa pura falla con identificadores exactos (una pregunta por "T1059.001" devolvía DC0059, S1059, G0059 con `granite-embedding:30m`); BM25 corrige justamente eso. Sobre las 6 preguntas de `eval/sample_questions.jsonl` medimos hit@5 = 4/6 (dense), 5/6 (sparse) y 6/6 (hybrid), por lo que el híbrido es el valor por defecto y el evaluador puede comparar las tres. Sin re‑ranking: puntos de extensión naturales en `pipeline.retrieve` (re‑ranker, HyDE, multi‑query) y `prompts.py`.
- Con `hybrid`, el `score` de cada contexto es el valor RRF (≈ 1/(60+rango) sumado), no una similitud coseno; con `dense` es coseno y con `sparse` el BM25 de Qdrant.
- **Desempate determinista** (`vectorstore.rank_hits`): los resultados se ordenan por score descendente y, en caso de empate, por `point_id` ascendente. Sin esta regla, los fragmentos empatados en la frontera del top‑k cambiaban de orden entre ejecuciones. `run_pilot.py --check-ties` verifica, sobre una corrida, que el top‑k de la traza coincide con una consulta posterior.
- **No determinismo de la generación**: aunque se use `temperature=0`, Ollama en CPU produjo respuestas distintas con contextos idénticos (19 de 36 en las réplicas de la corrida 2). Por eso la evaluación califica la traza guardada (`traces.jsonl`) de una corrida concreta, no una respuesta que se espere reproducir idéntica.
