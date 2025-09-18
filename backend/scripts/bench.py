from __future__ import annotations

import time
import numpy as np

from backend.app.config import get_settings
from backend.app.embeddings import EmbeddingService
from backend.app.vector_db import FlatVectorIndex


def main() -> None:
    settings = get_settings()
    index = FlatVectorIndex.load(settings.index_dir)
    emb = EmbeddingService(settings.embed_model, device=settings.device)
    q = "language models for enterprise"
    v = emb.encode([q])[0]
    t0 = time.perf_counter()
    _ = index.search(v, k=10, metric=settings.default_metric)
    dt = (time.perf_counter() - t0) * 1000
    print(f"Search latency: {dt:.2f} ms for N={index.size()} D={index.dimension}")


if __name__ == "__main__":
    main()


