"""Cliente mínimo para la API REST de Ollama (chat, embeddings, tags, pull)."""
from __future__ import annotations

import re
import time

import httpx

THINK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL)
# Familias que aceptan el parámetro `think` en /api/chat
THINKING_FAMILIES = ("qwen3", "deepseek-r1", "gpt-oss", "magistral")


def supports_thinking(model: str) -> bool:
    return any(model.lower().startswith(f) for f in THINKING_FAMILIES)


class OllamaClient:
    def __init__(self, base_url: str, timeout: float = 600):
        self.base_url = base_url.rstrip("/")
        self._c = httpx.Client(base_url=self.base_url, timeout=timeout)

    # ---------------------------------------------------------------- estado
    def is_alive(self) -> bool:
        try:
            return self._c.get("/api/tags").status_code == 200
        except httpx.HTTPError:
            return False

    def wait_alive(self, retries: int = 60, delay: float = 3.0) -> None:
        for _ in range(retries):
            if self.is_alive():
                return
            time.sleep(delay)
        raise RuntimeError(f"Ollama no responde en {self.base_url}")

    def list_models(self) -> list[str]:
        r = self._c.get("/api/tags")
        r.raise_for_status()
        return sorted(m["name"] for m in r.json().get("models", []))

    def has_model(self, name: str) -> bool:
        names = self.list_models()
        return name in names or f"{name}:latest" in names

    def pull(self, name: str) -> dict:
        r = self._c.post("/api/pull", json={"name": name, "stream": False}, timeout=None)
        r.raise_for_status()
        return r.json()

    # ------------------------------------------------------------ embeddings
    def embed(self, model: str, texts: list[str]) -> list[list[float]]:
        r = self._c.post("/api/embed", json={"model": model, "input": texts, "truncate": True})
        r.raise_for_status()
        return r.json()["embeddings"]

    # ------------------------------------------------------------------ chat
    def chat(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.1,
        num_ctx: int = 8192,
        num_predict: int = 1024,
        think: bool | None = None,
    ) -> dict:
        body: dict = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_ctx": num_ctx, "num_predict": num_predict},
        }
        if think is not None and supports_thinking(model):
            body["think"] = think

        r = self._c.post("/api/chat", json=body)
        if r.status_code == 400 and "think" in body:  # modelo sin soporte de thinking
            body.pop("think")
            r = self._c.post("/api/chat", json=body)
        r.raise_for_status()
        data = r.json()

        raw = data.get("message", {}).get("content", "")
        return {
            "content": THINK_RE.sub("", raw).strip(),
            "raw_content": raw,
            "thinking": data.get("message", {}).get("thinking"),
            "usage": {
                "prompt_tokens": data.get("prompt_eval_count"),
                "completion_tokens": data.get("eval_count"),
            },
            "timings_ms": {
                "load": (data.get("load_duration") or 0) / 1e6,
                "prompt_eval": (data.get("prompt_eval_duration") or 0) / 1e6,
                "eval": (data.get("eval_duration") or 0) / 1e6,
                "total": (data.get("total_duration") or 0) / 1e6,
            },
        }
