"""Vector math tests."""

import numpy as np
import pytest

from backend.app.rag.vector_search import bytes_to_vector, cosine_similarity, rank_vectors, vector_to_bytes


def test_cosine_identical_vectors() -> None:
    vec = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    assert cosine_similarity(vec, vec) == pytest.approx(1.0)


def test_rank_vectors_orders_desc() -> None:
    query = np.array([1.0, 0.0], dtype=np.float32)
    candidates = [
        ("low", np.array([0.0, 1.0], dtype=np.float32)),
        ("high", np.array([1.0, 0.0], dtype=np.float32)),
    ]
    ranked = rank_vectors(query, candidates, top_k=2)
    assert ranked[0][0] == "high"


def test_vector_bytes_roundtrip() -> None:
    vec = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    restored = bytes_to_vector(vector_to_bytes(vec), 3)
    assert np.allclose(vec, restored)
