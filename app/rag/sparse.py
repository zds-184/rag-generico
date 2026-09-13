"""Vectores dispersos tipo BM25 para búsqueda léxica en Qdrant.

Sólo se calcula aquí la parte "TF" (saturación BM25); la parte IDF la aplica Qdrant en el
servidor gracias a `Modifier.IDF` en la configuración del vector disperso. Los índices son
hashes estables (CRC32) del token, por lo que no hace falta vocabulario compartido.

El tokenizador conserva identificadores compuestos como "t1059.001" y además emite sus
partes ("t1059", "001"), de modo que una pregunta que cite un ID ATT&CK coincida
exactamente con los chunks que lo contienen.
"""
from __future__ import annotations

import re
import zlib
from collections import Counter

# \w es Unicode: conserva letras acentuadas (técnica, qué) y dígitos; admite ID compuestos (t1059.001, cmd.exe)
_TOKEN_RE = re.compile(r"\w+(?:[.\-/]\w+)*")
_SPLIT_RE = re.compile(r"[.\-_/]")

# Stopwords mínimas (inglés + español) para no premiar palabras vacías
STOPWORDS = frozenset(
    """a an and are as at be by for from has have in is it its of on or that the this to was were will with
    which who what when where how can may also into than then their there these those such not no
    el la los las un una unos unas de del y o que en es son por para con como se su sus al lo le les
    qué cual cuales cuál cuáles como cómo donde dónde cuando cuándo pero más muy este esta estos estas
    aplican aplica sobre entre hay ser está están""".split()
)


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for tok in _TOKEN_RE.findall(text.lower()):
        tokens.append(tok)
        parts = _SPLIT_RE.split(tok)
        if len(parts) > 1:
            # Partes del compuesto, salvo las puramente numéricas ("001" de T1059.001 coincidiría con todas las .001)
            tokens.extend(p for p in parts if len(p) > 1 and not p.isdigit())
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]


def token_index(token: str) -> int:
    return zlib.crc32(token.encode("utf-8")) & 0x7FFFFFFF


def document_sparse_vector(text: str, k1: float = 1.2, b: float = 0.75, avg_len: float = 256.0) -> tuple[list[int], list[float]]:
    """Pesos BM25 (sin IDF) por término para un chunk."""
    tokens = tokenize(text)
    length = len(tokens) or 1
    counts = Counter(tokens)
    indices, values = [], []
    for tok, tf in counts.items():
        indices.append(token_index(tok))
        values.append(tf * (k1 + 1) / (tf + k1 * (1 - b + b * length / avg_len)))
    return indices, values


def query_sparse_vector(text: str) -> tuple[list[int], list[float]]:
    """Consulta: presencia de término (peso 1); el IDF lo aporta Qdrant."""
    unique = sorted(set(tokenize(text)))
    return [token_index(t) for t in unique], [1.0] * len(unique)
