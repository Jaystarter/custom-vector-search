from __future__ import annotations

import argparse
import logging

from backend.app.config import get_settings
from backend.app.embeddings import EmbeddingService
from backend.app.loader import load_blogs
from backend.app.vector_db import FlatVectorIndex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
	parser = argparse.ArgumentParser(description="Rebuild the vector index from blogs.json")
	args = parser.parse_args()

	settings = get_settings()
	logger.info("Loading blogs from %s", settings.blog_json_path)
	entries = load_blogs(settings.blog_json_path)
	if not entries:
		raise SystemExit("No entries found")

	# No fallback: fail fast if model can't be loaded
	emb = EmbeddingService(settings.embed_model, device=settings.device)
	texts = [e["metadata"]["text"] for e in entries]
	vecs = emb.encode(texts, batch_size=settings.batch_size)
	index = FlatVectorIndex(dimension=int(vecs.shape[1]))
	for e, v in zip(entries, vecs):
		index.insert(e["id"], v, e["metadata"])
	index.save(settings.index_dir, model_name=emb.model_name, default_metric=settings.default_metric)
	logger.info("Saved index with %d vectors to %s", index.size(), settings.index_dir)


if __name__ == "__main__":
	main()
