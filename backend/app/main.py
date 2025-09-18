from __future__ import annotations

import logging
from pathlib import Path
import json
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .embeddings import EmbeddingService
from .loader import load_blogs
from .models import HealthResponse, SearchHit, SearchRequest, SearchResponse
from .vector_db import FlatVectorIndex

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Custom Vector Search", version="0.1.0")

settings = get_settings()
app.add_middleware(
	CORSMiddleware,
	allow_origins=settings.cors_origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

EMBEDDINGS: Optional[EmbeddingService] = None
INDEX: Optional[FlatVectorIndex] = None
ERROR_MESSAGE: Optional[str] = None


@app.on_event("startup")
def startup_event() -> None:
	global EMBEDDINGS, INDEX, ERROR_MESSAGE
	ERROR_MESSAGE = None
	# Try to initialize embeddings. Do not crash the server if model fails.
	try:
		EMBEDDINGS = EmbeddingService(
			settings.embed_model,
			max_seq_length=settings.max_seq_length,
			normalize_input=settings.normalize_input_text,
		)
	except Exception as e:  # surface error to API clients
		EMBEDDINGS = None
		ERROR_MESSAGE = (
			f"Failed to load embedding model '{settings.embed_model}': {e}. "
			"Verify the model id and any required Hugging Face auth token."
		)
		logger.error(ERROR_MESSAGE)

	index_dir = settings.index_dir
	# Try to load an existing index (supports old and new layouts via FlatVectorIndex.load)
	try:
		INDEX = FlatVectorIndex.load(index_dir)
		logger.info("Loaded index from %s", index_dir)
		# Ensure new two-file format JSON exists; write if missing (non-destructive migration)
		idx_json_path = index_dir / "index.json"
		if not idx_json_path.exists():
			try:
				payload = {
					"version": 1,
					"dimension": INDEX.dimension if hasattr(INDEX, "dimension") else 0,
					"model": (EMBEDDINGS.model_name if EMBEDDINGS else settings.embed_model),
					"default_metric": settings.default_metric,
					"created_at": datetime.utcnow().isoformat() + "Z",
					"ids": getattr(INDEX, "_ids", []),
					"metadatas": getattr(INDEX, "_metadatas", []),
				}
				with idx_json_path.open("w", encoding="utf-8") as f:
					json.dump(payload, f, ensure_ascii=False)
				logger.info("Wrote %s for two-file index format", idx_json_path)
			except Exception as e:
				logger.warning("Failed to write index.json: %s", e)
		return
	except FileNotFoundError:
		logger.info("No existing index found in %s; building from blog.json if possible", index_dir)

	# Build index from blogs.json if we have an embedding model
	if EMBEDDINGS is None:
		logger.warning("Embedding model unavailable; skipping index build")
		return
	logger.info("Building index from %s", settings.blog_json_path)
	entries = load_blogs(settings.blog_json_path)
	if not entries:
		raise RuntimeError("No blog entries found to index")
	texts = [e["metadata"]["text"] for e in entries]
	emb = EMBEDDINGS.encode(texts, batch_size=settings.batch_size, normalize=False)
	if emb.ndim != 2:
		raise RuntimeError("Embeddings must be 2D")
	INDEX = FlatVectorIndex(dimension=int(emb.shape[1]))
	for e, v in zip(entries, emb):
		INDEX.insert(e["id"], v, e["metadata"])
	INDEX.save(index_dir, model_name=EMBEDDINGS.model_name, default_metric=settings.default_metric)  # type: ignore[arg-type]
	logger.info("Index built with %d vectors", INDEX.size())


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
	return HealthResponse()


@app.get("/posts", response_model=SearchResponse)
def list_posts() -> SearchResponse:
	if ERROR_MESSAGE:
		raise HTTPException(status_code=503, detail=ERROR_MESSAGE)
	if INDEX is None:
		raise HTTPException(status_code=503, detail="index not ready")
	# Access aligned ids and metadatas from the in-memory index
	results = [
		SearchHit(id=i, text=m.get("text", ""), score=0.0)
		for i, m in zip(getattr(INDEX, "_ids", []), getattr(INDEX, "_metadatas", []))
	]
	return SearchResponse(results=results)


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest) -> SearchResponse:
	if not req.query:
		raise HTTPException(status_code=400, detail="query must not be empty")
	if ERROR_MESSAGE:
		raise HTTPException(status_code=503, detail=ERROR_MESSAGE)
	if INDEX is None or EMBEDDINGS is None:
		raise HTTPException(status_code=503, detail="index not ready")
	metric = req.metric or settings.default_metric
	emb = EMBEDDINGS.encode([req.query], batch_size=1, normalize=bool(req.normalize))
	vector = emb[0]
	try:
		results = INDEX.search(vector, k=req.k, metric=metric, normalize_scores=bool(req.normalize))  # type: ignore[arg-type]
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))
	hits = [
		SearchHit(id=r[0], text=r[2].get("text", ""), score=r[1])
		for r in results
	]
	return SearchResponse(results=hits)
