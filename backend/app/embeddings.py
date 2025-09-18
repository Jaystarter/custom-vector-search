from __future__ import annotations

import logging
from typing import Iterable, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from .preprocess import normalize_text

logger = logging.getLogger(__name__)


class EmbeddingService:
	def __init__(self, model_name: str, device: str = "default", max_seq_length: int | None = 512, normalize_input: bool = True) -> None:
		self.model_name = model_name
		# Keep a simple default to minimize complexity; let the library decide the device
		self.device = "default"
		self.model = self._load_model(model_name)
		if max_seq_length:
			try:
				self.model.max_seq_length = int(max_seq_length)  # type: ignore[attr-defined]
			except Exception:
				pass
		self.normalize_input = normalize_input

	def _load_model(self, model_name: str) -> SentenceTransformer:
		logger.info("Loading embedding model %s", model_name)
		# No fallback and no explicit device: use library defaults (typically CPU)
		return SentenceTransformer(model_name)

	def encode(self, texts: Iterable[str], batch_size: int = 64, normalize: bool = False) -> np.ndarray:
		if self.normalize_input:
			texts = [normalize_text(t) for t in texts]
		emb = self.model.encode(
			list(texts),
			batch_size=batch_size,
			normalize_embeddings=normalize,
			convert_to_numpy=True,
			show_progress_bar=False,
		)
		return np.asarray(emb, dtype=np.float32)
