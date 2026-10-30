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
    """Divide un párrafo demasiado largo por oraciones; si una oración excede, por caracteres.

    Los trozos por caracteres NO se solapan entre sí: el solape lo añade `split_text` una sola vez
    (antes se añadía aquí y otra vez allí, y el texto de solape quedaba duplicado en los documentos
    largos). Se reserva sitio para ese solape y el separador para que el chunk no exceda `chunk_size`.
    """
    pieces: list[str] = []
    piece_size = max(1, chunk_size - overlap - 2)
    for sentence in _SENTENCE_RE.split(text):
        if len(sentence) <= piece_size:
            pieces.append(sentence)
            continue
        start = 0
        while start < len(sentence):
            end = min(start + piece_size, len(sentence))
            if end < len(sentence):
                # Cortar en un espacio para no partir palabras (el separador "\n\n" reemplaza a ese espacio)
                cut = sentence.rfind(" ", start + piece_size // 2, end)
                if cut != -1:
                    end = cut
            pieces.append(sentence[start:end].strip())
            start = end
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
            # El solape se recorta si hace falta para que tail + separador + piece quepa en chunk_size
            tail = _tail(current, min(chunk_overlap, chunk_size - 2 - len(piece)))
            current = f"{tail}\n\n{piece}" if tail else piece
    if current:
        chunks.append(current)
    return chunks
