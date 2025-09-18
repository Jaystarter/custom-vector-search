from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Literal, Optional, Tuple

import numpy as np

Metric = Literal["cosine", "dot", "euclidean"]


@dataclass
class VectorRecord:
	id: str
	vector: np.ndarray
	metadata: Dict


class FlatVectorIndex:
	"""Simple flat index for dense vectors.

	- Insert and bulk insert records
	- Search top-k by cosine, dot, or euclidean distance
	- Persist/Load to/from disk
	"""

	def __init__(self, dimension: int) -> None:
		self.dimension: int = int(dimension)
		self._ids: List[str] = []
		self._metadatas: List[Dict] = []
		self._vectors_list: List[np.ndarray] = []
		self._normed_list: List[np.ndarray] = []
		self._sqnorm_list: List[float] = []

		self._vectors: Optional[np.ndarray] = None
		self._normed: Optional[np.ndarray] = None
		self._sqnorms: Optional[np.ndarray] = None
		self._dirty: bool = False

	def size(self) -> int:
		return len(self._ids)

	@staticmethod
	def _as_f32(vector: np.ndarray) -> np.ndarray:
		v = np.asarray(vector, dtype=np.float32)
		if v.ndim != 1:
			raise ValueError("vector must be 1D")
		return v

	def insert(self, record_id: str, vector: np.ndarray, metadata: Dict) -> None:
		v = self._as_f32(vector)
		if v.shape[0] != self.dimension:
			raise ValueError(f"vector dim {v.shape[0]} != index dim {self.dimension}")
		norm = np.linalg.norm(v)
		if norm == 0.0:
			raise ValueError("zero vector cannot be inserted")
		nv = v / (norm + 1e-12)
		self._ids.append(record_id)
		self._metadatas.append(metadata)
		self._vectors_list.append(v)
		self._normed_list.append(nv)
		self._sqnorm_list.append(float(norm**2))
		self._dirty = True

	def bulk_insert(self, records: Iterable[VectorRecord]) -> None:
		for rec in records:
			self.insert(rec.id, rec.vector, rec.metadata)

	def _materialize(self) -> None:
		if not self._dirty and self._vectors is not None:
			return
		if not self._vectors_list:
			self._vectors = np.empty((0, self.dimension), dtype=np.float32)
			self._normed = np.empty((0, self.dimension), dtype=np.float32)
			self._sqnorms = np.empty((0,), dtype=np.float32)
			self._dirty = False
			return
		self._vectors = np.vstack(self._vectors_list).astype(np.float32, copy=False)
		self._normed = np.vstack(self._normed_list).astype(np.float32, copy=False)
		self._sqnorms = np.asarray(self._sqnorm_list, dtype=np.float32)
		self._dirty = False

	def _top_k(self, scores: np.ndarray, k: int) -> np.ndarray:
		k = min(k, scores.size)
		if k <= 0:
			return np.empty((0,), dtype=np.int64)
		idx = np.argpartition(scores, -k)[-k:]
		# sort selected indices by score desc
		order = np.argsort(scores[idx])[::-1]
		return idx[order]

	def search(self, query: np.ndarray, k: int, metric: Metric = "cosine", normalize_scores: bool = False) -> List[Tuple[str, float, Dict]]:
		self._materialize()
		assert self._vectors is not None and self._normed is not None and self._sqnorms is not None
		q = self._as_f32(query)
		if q.shape[0] != self.dimension:
			raise ValueError(f"query dim {q.shape[0]} != index dim {self.dimension}")
		norm_q = np.linalg.norm(q)
		if norm_q == 0.0:
			raise ValueError("zero query vector")

		if metric == "cosine":
			qn = q / (norm_q + 1e-12)
			scores = self._normed @ qn  # in [-1,1]
			if normalize_scores:
				scores = 0.5 * (scores + 1.0)  # -> [0,1]
		elif metric == "dot":
			scores = self._vectors @ q
			if normalize_scores:
				# convert to cosine-like by dividing by norms, then map to [0,1]
				norms = np.sqrt(self._sqnorms) * (norm_q + 1e-12)
				cos = scores / (norms + 1e-12)
				scores = 0.5 * (cos + 1.0)
		elif metric == "euclidean":
			# lower distance is better
			d2 = self._sqnorms + (norm_q**2) - 2.0 * (self._vectors @ q)
			if normalize_scores:
				# map distance to similarity [0,1]
				scores = 1.0 / (1.0 + np.sqrt(np.maximum(d2, 0.0)))
			else:
				# use negative squared distance as score for ranking
				scores = -d2
		else:
			raise ValueError(f"unknown metric: {metric}")

		idx = self._top_k(scores, k)
		return [
			(self._ids[i], float(scores[i]), self._metadatas[i])
			for i in idx
		]

	def save(self, directory: Path, model_name: str, default_metric: Metric) -> None:
		directory.mkdir(parents=True, exist_ok=True)
		self._materialize()
		assert self._vectors is not None and self._normed is not None and self._sqnorms is not None
		(np.savez_compressed)(
			str(directory / "data.npz"),
			vectors=self._vectors,
			normed=self._normed,
			sqnorms=self._sqnorms,
		)
		index_json = {
			"version": 1,
			"dimension": self.dimension,
			"model": model_name,
			"default_metric": default_metric,
			"created_at": datetime.utcnow().isoformat() + "Z",
			"ids": self._ids,
			"metadatas": self._metadatas,
		}
		with (directory / "index.json").open("w", encoding="utf-8") as f:
			json.dump(index_json, f, ensure_ascii=False)

	@classmethod
	def load(cls, directory: Path) -> "FlatVectorIndex":
		data_path = directory / "data.npz"
		index_path = directory / "index.json"
		# Back-compat paths (older layout)
		ids_path = directory / "ids.json"
		meta_path = directory / "metadatas.json"
		man_path = directory / "manifest.json"

		if not data_path.exists():
			raise FileNotFoundError("data.npz is missing")

		with np.load(str(data_path)) as z:
			vectors = z["vectors"].astype(np.float32, copy=False)
			normed = z["normed"].astype(np.float32, copy=False)
			sqnorms = z["sqnorms"].astype(np.float32, copy=False)

		# Prefer new single JSON manifest
		if index_path.exists():
			with index_path.open("r", encoding="utf-8") as f:
				idx_json = json.load(f)
			ids: List[str] = idx_json.get("ids", [])
			metadatas: List[Dict] = idx_json.get("metadatas", [])
		else:
			# Older layout: separate files
			if not (ids_path.exists() and meta_path.exists() and man_path.exists()):
				raise FileNotFoundError("index metadata files are missing")
			with ids_path.open("r", encoding="utf-8") as f:
				ids = json.load(f)
			with meta_path.open("r", encoding="utf-8") as f:
				metadatas = json.load(f)

		if vectors.ndim != 2:
			raise ValueError("vectors must be 2D")
		idx = cls(dimension=vectors.shape[1])
		idx._vectors = vectors
		idx._normed = normed
		idx._sqnorms = sqnorms
		idx._ids = ids
		idx._metadatas = metadatas
		idx._vectors_list = []
		idx._normed_list = []
		idx._sqnorm_list = []
		idx._dirty = False
		return idx
