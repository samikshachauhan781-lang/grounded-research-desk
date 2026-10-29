"""Sliding-window chunker with overlap."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkDraft:
    chunk_index: int
    text: str
    char_start: int
    char_end: int


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[ChunkDraft]:
    if not text:
        return []
    if len(text) <= chunk_size:
        return [ChunkDraft(0, text, 0, len(text))]

    chunks: list[ChunkDraft] = []
    start = 0
    index = 0
    step = max(1, chunk_size - overlap)
    while start < len(text):
        end = min(len(text), start + chunk_size)
        piece = text[start:end]
        if piece.strip():
            chunks.append(ChunkDraft(index, piece, start, end))
            index += 1
        if end >= len(text):
            break
        start += step
    return chunks
