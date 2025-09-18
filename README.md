# custom-vector-search
Minimal semantic search app using FastAPI + TaylorAI/bge-micro. Builds a flat in-memory vector index from blogs.json, supports cosine/dot/L2, and exposes a /search API with a tiny UI. Pure Python/NumPy—no FAISS or external vector DB. Caching and basic tests included.
