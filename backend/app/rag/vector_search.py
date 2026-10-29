"""Cosine similarity search helpers."""

import numpy as np


def bytes_to_vector(data: bytes, dimension: int) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.float32)
    if arr.shape[0] != dimension:
        msg = f"Vector dimension mismatch: expected {dimension}, got {arr.shape[0]}"
        raise ValueError(msg)
    return arr


def vector_to_bytes(vec: np.ndarray) -> bytes:
    if not np.all(np.isfinite(vec)):
        msg = "Vector contains non-finite values"
        raise ValueError(msg)
    return vec.astype(np.float32).tobytes()


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    score = float(np.dot(a, b) / (norm_a * norm_b))
    if not np.isfinite(score):
        return 0.0
    return score


def rank_vectors(
    query: np.ndarray,
    candidates: list[tuple[str, np.ndarray]],
    top_k: int,
    min_score: float | None = None,
) -> list[tuple[str, float]]:
    scored: list[tuple[str, float]] = []
    for chunk_id, vec in candidates:
        score = cosine_similarity(query, vec)
        if min_score is not None and score < min_score:
            continue
        scored.append((chunk_id, score))
    scored.sort(key=lambda item: (-item[1], item[0]))
    return scored[:top_k]
