# RAG genérico local sobre MITRE ATT&CK

Arquitectura RAG **deliberadamente genérica** (chunking por caracteres → embeddings + BM25 → búsqueda top‑k híbrida/densa/léxica → prompt con contexto → LLM), 100 % local con Docker Compose, pensada para servir como *sistema bajo prueba* de un evaluador de RAG.

| Componente | Tecnología | Puerto |
|---|---|---|
| LLM + embeddings | [Ollama](https://ollama.com) (`qwen3:4b-instruct` por defecto, `granite-embedding:30m`) | 11434 |
| Base vectorial | [Qdrant](https://qdrant.tech) | 6333 (REST/dashboard), 6334 (gRPC) |
| API | FastAPI (`/query`, `/retrieve`, `/models`, `/collection`, `/health`) | 8000 |
| Interfaz web | Streamlit, selector **RAG / Solo LLM / Comparar ambos** | 8501 |
| Corpus | MITRE ATT&CK STIX 2.1 desde `mitre-attack/attack-stix-data` (siempre la última versión) | — |

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
| `LLM_TEMPERATURE`, `LLM_NUM_CTX`, `LLM_NUM_PREDICT` | Parámetros de generación | `0.1`, `4096`, `1024` |
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
  "model": "qwen3:4b",           // opcional, cualquier modelo cargado en Ollama
  "temperature": 0.1,
  "filters": {"object_type": ["technique", "sub-technique"]},   // opcional
  "think": false,
  "retrieval": "hybrid",         // "hybrid" | "dense" | "sparse" (opcional; por defecto RETRIEVAL_MODE)
  "include_prompt": true
}
```

Respuesta (todo lo necesario para métricas de retrieval y generación):

```json
{
  "question": "...", "mode": "rag", "model": "qwen3:4b",
  "answer": "...",
  "contexts": [
    {"rank": 1, "score": 0.83, "point_id": "...", "text": "...",
     "metadata": {"attack_id": "T1059.001", "name": "PowerShell", "object_type": "sub-technique",
                  "domain": "enterprise-attack", "attack_version": "17.1", "url": "https://attack.mitre.org/techniques/T1059/001",
                  "tactics": ["execution"], "platforms": ["Windows"], "chunk_index": 0, "n_chunks": 3}}
  ],
  "prompt": {"system": "...", "user": "..."},
  "usage": {"prompt_tokens": 1834, "completion_tokens": 212},
  "timings_ms": {"retrieval": 41.2, "generation": 5321.0, "total": 5362.2, "ollama": {...}},
  "params": {"top_k": 5, "temperature": 0.1, "think": false, "embed_model": "nomic-embed-text", "collection": "mitre_attack", "filters": {}}
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
├─ eval/                     # cliente de ejemplo + preguntas de muestra
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

Para usar un Ollama ya instalado en Windows en lugar del contenedor: en `.env` pon `OLLAMA_URL=http://host.docker.internal:11434`, descarga los modelos con `ollama pull qwen3:4b` y `ollama pull nomic-embed-text` en el host, y arranca sin los servicios de Ollama: `docker compose up -d qdrant api ui` seguido de `docker compose run --rm --no-deps ingest`.

## Notas de diseño para la evaluación

- Los dos modos comparten *persona*, modelo, temperatura y parámetros; sólo difiere el grounding del prompt. Así la diferencia RAG vs LLM se atribuye al contexto recuperado.
- Cada respuesta devuelve el prompt exacto, los chunks con `score` y metadatos, tokens y tiempos: suficiente para faithfulness, answer relevancy, context precision/recall y coste/latencia.
- El retrieval ofrece tres estrategias seleccionables por petición: `dense` (coseno sobre embeddings), `sparse` (BM25: TF en cliente, IDF en Qdrant) e `hybrid` (ambas + Reciprocal Rank Fusion). La densa pura falla con identificadores exactos (una pregunta por "T1059.001" devolvía DC0059, S1059, G0059 con `granite-embedding:30m`); BM25 corrige justamente eso. Sobre las 6 preguntas de `eval/sample_questions.jsonl` medimos hit@5 = 4/6 (dense), 5/6 (sparse) y 6/6 (hybrid), por lo que el híbrido es el valor por defecto y el evaluador puede comparar las tres. Sin re‑ranking: puntos de extensión naturales en `pipeline.retrieve` (re‑ranker, HyDE, multi‑query) y `prompts.py`.
- Con `hybrid`, el `score` de cada contexto es el valor RRF (≈ 1/(60+rango) sumado), no una similitud coseno; con `dense` es coseno y con `sparse` el BM25 de Qdrant.
