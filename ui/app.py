"""Interfaz web (Streamlit) del RAG genérico sobre MITRE ATT&CK.

Permite elegir si la respuesta se genera con RAG (recuperación + LLM), sólo con el LLM,
o comparar ambos modos lado a lado con la misma pregunta y el mismo modelo.
"""
from __future__ import annotations

import os
import time

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
OBJECT_TYPES = [
    "technique", "sub-technique", "group", "software", "mitigation",
    "tactic", "campaign", "detection-strategy", "data-source", "data-component",
]
DOMAINS = ["enterprise-attack", "mobile-attack", "ics-attack"]

st.set_page_config(page_title="RAG MITRE ATT&CK", page_icon="🛡️", layout="wide")


# ------------------------------------------------------------------ helpers
@st.cache_data(ttl=15)
def api_get(path: str) -> dict | None:
    try:
        r = requests.get(f"{API_URL}{path}", timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None


def api_post(path: str, body: dict, timeout: int = 1800) -> dict:
    r = requests.post(f"{API_URL}{path}", json=body, timeout=timeout)
    if r.status_code >= 400:
        try:
            detail = r.json().get("detail", r.text)
        except ValueError:
            detail = r.text
        raise RuntimeError(f"HTTP {r.status_code}: {detail}")
    return r.json()


def render_result(res: dict, show_prompt: bool, show_thinking: bool) -> None:
    t = res["timings_ms"]
    usage = res.get("usage") or {}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Modo", res["mode"].upper())
    c2.metric("Total", f"{t['total']/1000:.1f} s")
    c3.metric("Retrieval", f"{t['retrieval']:.0f} ms")
    c4.metric("Tokens (in/out)", f"{usage.get('prompt_tokens') or '-'} / {usage.get('completion_tokens') or '-'}")

    st.markdown("**Respuesta**")
    st.markdown(res["answer"] or "_(respuesta vacía)_")

    if show_thinking and res.get("thinking"):
        with st.expander("🧠 Razonamiento del modelo"):
            st.markdown(res["thinking"])

    if res["mode"] == "rag":
        label_ret = res.get("params", {}).get("retrieval") or "-"
        with st.expander(f"📚 Contextos recuperados ({len(res['contexts'])}) · recuperación: {label_ret}", expanded=False):
            for c in res["contexts"]:
                m = c["metadata"]
                label = " - ".join(x for x in (m.get("attack_id"), m.get("name")) if x) or m.get("doc_id", "")
                st.markdown(
                    f"**[{c['rank']}] {label}** &nbsp;·&nbsp; score `{c['score']:.4f}` &nbsp;·&nbsp; "
                    f"`{m.get('object_type')}` &nbsp;·&nbsp; chunk {m.get('chunk_index', 0) + 1}/{m.get('n_chunks', 1)}"
                    + (f" &nbsp;·&nbsp; [ATT&CK]({m['url']})" if m.get("url") else "")
                )
                st.text(c["text"])
                st.divider()

    if show_prompt and res.get("prompt"):
        with st.expander("📝 Prompt enviado al LLM"):
            st.code(f"[system]\n{res['prompt']['system']}\n\n[user]\n{res['prompt']['user']}", language="text")


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.title("🛡️ RAG MITRE ATT&CK")
    health = api_get("/health")
    if health is None:
        st.error(f"API no disponible en {API_URL}")
        st.stop()

    coll = health["qdrant"].get("collection", {})
    points = coll.get("points_count", 0)
    if health["status"] == "ok" and not health.get("ingest_complete", True):
        st.warning(f"Ingesta en curso: {points:,} chunks indexados hasta ahora. El modo RAG ya responde, pero con corpus parcial.")
    elif health["status"] == "ok":
        st.success(f"Colección `{coll.get('name')}`: {points:,} chunks")
    else:
        st.warning("Sistema degradado: revisa Ollama / Qdrant / ingesta")
        st.json(health, expanded=False)

    st.subheader("Modo de respuesta")
    mode_label = st.radio(
        "¿Cómo generar la respuesta?",
        ["RAG (recuperación + LLM)", "Solo LLM", "Comparar ambos"],
        index=0,
        label_visibility="collapsed",
    )

    st.subheader("Modelo")
    models = health["ollama"].get("models", [])
    default_model = health["defaults"]["llm_model"]
    embed_model = health["defaults"]["embed_model"]
    llm_choices = [m for m in models if not any(k in m for k in ("embed", "minilm", "bge", "arctic"))] or [default_model]
    # Preselección: coincidencia exacta del modelo por defecto; si no, misma familia
    idx = next((i for i, m in enumerate(llm_choices) if m in (default_model, f"{default_model}:latest")), None)
    if idx is None:
        idx = next((i for i, m in enumerate(llm_choices) if m.split(":")[0] == default_model.split(":")[0]), 0)
    model = st.selectbox("LLM", llm_choices, index=idx)
    st.caption(f"Embeddings: `{embed_model}`")

    with st.expander("➕ Descargar otro modelo"):
        new_model = st.text_input("Nombre en Ollama", placeholder="llama3.1:8b")
        if st.button("Descargar", use_container_width=True) and new_model:
            with st.spinner(f"Descargando {new_model}..."):
                try:
                    api_post("/models/pull", {"model": new_model}, timeout=3600)
                    api_get.clear()
                    st.success("Listo. Recarga la página.")
                except Exception as exc:  # noqa: BLE001
                    st.error(str(exc))

    st.subheader("Parámetros")
    RETRIEVAL_LABELS = {"hybrid": "Híbrida (densa + BM25, RRF)", "dense": "Densa (embeddings)", "sparse": "BM25 (léxica)"}
    default_retrieval = health["defaults"].get("retrieval", "hybrid")
    retrieval = st.selectbox(
        "Recuperación",
        list(RETRIEVAL_LABELS),
        index=list(RETRIEVAL_LABELS).index(default_retrieval) if default_retrieval in RETRIEVAL_LABELS else 0,
        format_func=RETRIEVAL_LABELS.get,
    )
    top_k = st.slider("Top-K contextos", 1, 20, int(health["defaults"]["top_k"]))
    temperature = st.slider("Temperatura", 0.0, 1.5, float(health["defaults"]["temperature"]), 0.05)
    think = st.toggle("Modo thinking (qwen3 / deepseek-r1)", value=bool(health["defaults"]["think"]))

    with st.expander("🔎 Filtros de recuperación"):
        f_types = st.multiselect("Tipo de objeto", OBJECT_TYPES)
        f_domains = st.multiselect("Dominio", DOMAINS)
    filters = {k: v for k, v in {"object_type": f_types, "domain": f_domains}.items() if v}

    show_prompt = st.checkbox("Mostrar prompt", value=False)
    show_thinking = st.checkbox("Mostrar razonamiento", value=False)

# ------------------------------------------------------------------ main
st.header("Pregunta sobre MITRE ATT&CK")
st.caption(
    "Corpus: MITRE ATT&CK STIX 2.1 (última versión publicada) · Vector DB: Qdrant · LLM/embeddings: Ollama. "
    "La API está en `/docs` para integrar un evaluador."
)

examples = [
    "¿Qué es la técnica T1059.001 y cómo se mitiga?",
    "Which groups are known to use Mimikatz and for what techniques?",
    "¿Qué técnicas de persistencia usa APT29?",
    "How can Kerberoasting (T1558.003) be detected?",
    "¿Qué mitigaciones aplican a Phishing (T1566)?",
]
with st.expander("💡 Ejemplos de preguntas"):
    for ex in examples:
        if st.button(ex, key=f"ex_{hash(ex)}"):
            st.session_state["question"] = ex

question = st.text_area("Pregunta", key="question", height=90, placeholder="Escribe tu pregunta...")
ask = st.button("Consultar", type="primary", disabled=not question.strip())

if ask and question.strip():
    base = {
        "question": question.strip(),
        "top_k": top_k,
        "model": model,
        "temperature": temperature,
        "filters": filters or None,
        "think": think,
        "retrieval": retrieval,
        "include_prompt": True,
    }
    if mode_label == "Comparar ambos":
        col_rag, col_llm = st.columns(2)
        for col, mode in ((col_rag, "rag"), (col_llm, "llm")):
            with col:
                st.subheader("🔗 RAG" if mode == "rag" else "🧠 Solo LLM")
                with st.spinner(f"Generando ({mode})..."):
                    try:
                        res = api_post("/query", {**base, "mode": mode})
                        render_result(res, show_prompt, show_thinking)
                    except Exception as exc:  # noqa: BLE001
                        st.error(str(exc))
    else:
        mode = "rag" if mode_label.startswith("RAG") else "llm"
        with st.spinner(f"Generando ({mode}) con {model}..."):
            t0 = time.perf_counter()
            try:
                res = api_post("/query", {**base, "mode": mode})
                render_result(res, show_prompt, show_thinking)
                st.session_state.setdefault("history", []).insert(
                    0, {"q": question.strip(), "mode": mode, "model": model, "answer": res["answer"],
                        "secs": round(time.perf_counter() - t0, 1)}
                )
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))

if st.session_state.get("history"):
    st.divider()
    st.subheader("Historial de la sesión")
    for h in st.session_state["history"][:10]:
        with st.expander(f"[{h['mode'].upper()} · {h['model']} · {h['secs']} s] {h['q']}"):
            st.markdown(h["answer"])
