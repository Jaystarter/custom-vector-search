from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.loader import load_blogs
from backend.app.main import app
from backend.app.vector_db import FlatVectorIndex


def test_loader_matches_blog_json():
	settings = get_settings()
	entries = load_blogs(settings.blog_json_path)
	with settings.blog_json_path.open("r", encoding="utf-8") as f:
		raw = json.load(f)

	# Blog loader should return every valid entry from blog.json
	assert isinstance(raw, list) and len(raw) > 0
	assert len(entries) == len(raw)
	assert {e["id"] for e in entries} == {r["id"] for r in raw}

	# Sanity-check some expected content is present (data-specific assertions)
	texts = [e["metadata"]["text"].lower() for e in entries]
	assert any("seed round" in t for t in texts)
	assert any("rag" in t or "retrieval augmented generation" in t for t in texts)
	assert any("careers" in t or "hiring" in t for t in texts)


def test_posts_lists_index_contents(monkeypatch: pytest.MonkeyPatch):
	settings = get_settings()
	# Ensure transient model load failures do not block /posts in tests
	import backend.app.main as m
	# Stub EmbeddingService before TestClient triggers startup
	class _NoopEmb:
		def __init__(self, *a, **k):
			self.model_name = "fake"
		def encode(self, texts, batch_size: int = 1, normalize: bool = False):
			arr = np.zeros((len(list(texts)), 3), dtype=np.float32)
			return arr
	monkeypatch.setattr(m, "EmbeddingService", _NoopEmb, raising=False)
	monkeypatch.setattr(m, "ERROR_MESSAGE", None, raising=False)

	# Use module's app to avoid mismatched references, and ensure INDEX is set
	client = TestClient(m.app)
	try:
		m.INDEX = FlatVectorIndex.load(settings.index_dir)
	except Exception:
		# Fall back to a tiny empty index to avoid 503; tests below only check count/text presence
		m.INDEX = FlatVectorIndex(3)
	
	r = client.get("/posts")
	assert r.status_code == 200
	data = r.json().get("results", [])

	# Compare count with persisted index manifest for determinism
	idx_path = settings.index_dir / "index.json"
	with idx_path.open("r", encoding="utf-8") as f:
		idx_json = json.load(f)
	expected_len = len(idx_json.get("ids", []))
	assert len(data) == expected_len

	# Spot-check a couple of known entries from blog.json are present in /posts
	ids = {d["id"] for d in data}
	texts = [d["text"].lower() for d in data]
	assert "b4978d59-17a8-4ffb-a196-d3064db964e6" in ids  # seed round
	assert any("seed round" in t for t in texts)
	assert any("rag" in t for t in texts)


def test_search_returns_expected_for_seed_rag_careers(monkeypatch: pytest.MonkeyPatch):
	# Build a tiny, deterministic in-memory index with three representative docs
	import backend.app.main as m

	settings = get_settings()
	with settings.blog_json_path.open("r", encoding="utf-8") as f:
		blog = json.load(f)

	# Pick three data-specific posts by content
	seed_item = next(x for x in blog if "seed round" in x["metadata"]["text"].lower())
	rag_item = next(x for x in blog if ("rag" in x["metadata"]["text"].lower() or "retrieval augmented generation" in x["metadata"]["text"].lower()))
	careers_item = next(x for x in blog if ("careers" in x["metadata"]["text"].lower() or "hiring" in x["metadata"]["text"].lower()))

	idx = FlatVectorIndex(3)
	idx.insert(seed_item["id"], np.array([1.0, 0.0, 0.0], dtype=np.float32), {"text": seed_item["metadata"]["text"]})
	idx.insert(rag_item["id"], np.array([0.0, 1.0, 0.0], dtype=np.float32), {"text": rag_item["metadata"]["text"]})
	idx.insert(careers_item["id"], np.array([0.0, 0.0, 1.0], dtype=np.float32), {"text": careers_item["metadata"]["text"]})

	class FakeEmbedding:
		def __init__(self) -> None:
			self.model_name = "fake"

		def encode(self, texts, batch_size: int = 1, normalize: bool = False):  # noqa: D401
			out = []
			for t in list(texts):
				lt = str(t).lower()
				if "seed" in lt or "$20m" in lt:
					out.append(np.array([1.0, 0.0, 0.0], dtype=np.float32))
				elif "rag" in lt or "retrieval augmented generation" in lt:
					out.append(np.array([0.0, 1.0, 0.0], dtype=np.float32))
				elif "career" in lt or "hiring" in lt:
					out.append(np.array([0.0, 0.0, 1.0], dtype=np.float32))
				else:
					out.append(np.array([0.33, 0.33, 0.33], dtype=np.float32))
			return np.vstack(out)

	# Stub heavy embedding load before TestClient to prevent model download
	monkeypatch.setattr(m, "EmbeddingService", lambda *a, **k: FakeEmbedding(), raising=False)
	client = TestClient(m.app)
	# Override globals after app startup (ensure our deterministic setup)
	monkeypatch.setattr(m, "INDEX", idx, raising=False)
	monkeypatch.setattr(m, "EMBEDDINGS", FakeEmbedding(), raising=False)
	monkeypatch.setattr(m, "ERROR_MESSAGE", None, raising=False)

	def _top1(query: str) -> dict:
		resp = client.post("/search", json={"query": query, "k": 1})
		assert resp.status_code == 200
		payload = resp.json()
		assert payload.get("results")
		return payload["results"][0]

	res_seed = _top1("seed round funding announcement")
	assert res_seed["id"] == seed_item["id"]
	assert "seed" in res_seed["text"].lower()

	res_rag = _top1("explain RAG approach")
	assert res_rag["id"] == rag_item["id"]
	assert "rag" in res_rag["text"].lower() or "retrieval augmented generation" in res_rag["text"].lower()

	res_careers = _top1("Where is your careers portal?")
	assert res_careers["id"] == careers_item["id"]
	assert "career" in res_careers["text"].lower() or "hiring" in res_careers["text"].lower()


