from __future__ import annotations

import numpy as np

from backend.app.vector_db import FlatVectorIndex


def test_metrics_and_topk():
    dim = 3
    idx = FlatVectorIndex(dim)
    # simple orthogonal vectors
    idx.insert("a", np.array([1.0, 0.0, 0.0], dtype=np.float32), {"text": "A"})
    idx.insert("b", np.array([0.0, 1.0, 0.0], dtype=np.float32), {"text": "B"})
    idx.insert("c", np.array([0.0, 0.0, 1.0], dtype=np.float32), {"text": "C"})

    q = np.array([1.0, 0.1, 0.0], dtype=np.float32)

    cos = idx.search(q, k=2, metric="cosine")
    assert cos[0][0] == "a"

    dot = idx.search(q, k=2, metric="dot")
    assert dot[0][0] == "a"

    l2 = idx.search(q, k=2, metric="euclidean")
    assert l2[0][0] == "a"


