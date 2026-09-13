"""Chunking genérico por caracteres, respetando párrafos y oraciones."""
from __future__ import annotations

import re

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def _tail(text: str, overlap: int) -> str:
    """Devuelve los últimos `overlap` caracteres, cortados en un límite de palabra."""
    if overlap <= 0:
        return ""
    if len(text) <= overlap:
        return text
    tail = text[-overlap:]
    cut = tail.find(" ")
    return tail[cut + 1 :] if cut != -1 else tail


def _hard_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Divide un párrafo demasiado largo por oraciones; si una oración excede, por caracteres."""
    pieces: list[str] = []
    for sentence in _SENTENCE_RE.split(text):
        if len(sentence) <= chunk_size:
            pieces.append(sentence)
        else:
            step = max(1, chunk_size - overlap)
            pieces.extend(sentence[i : i + chunk_size] for i in range(0, len(sentence), step))
    return pieces


def split_text(text: str, chunk_size: int = 1200, chunk_overlap: int = 150) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    pieces: list[str] = []
    for para in re.split(r"\n{2,}", text):
        para = para.strip()
        if not para:
            continue
        if len(para) <= chunk_size:
            pieces.append(para)
        else:
            pieces.extend(_hard_split(para, chunk_size, chunk_overlap))

    chunks: list[str] = []
    current = ""
    for piece in pieces:
        if not current:
            current = piece
        elif len(current) + 2 + len(piece) <= chunk_size:
            current = f"{current}\n\n{piece}"
        else:
            chunks.append(current)
            tail = _tail(current, chunk_overlap)
            current = f"{tail}\n\n{piece}" if tail else piece
    if current:
        chunks.append(current)
    return chunks
