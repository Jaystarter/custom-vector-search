from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _project_root() -> Path:
	return Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
	model_config = SettingsConfigDict(
		env_file=(
			str(_project_root() / ".env"),
			str(_project_root() / "backend" / ".env"),
		),
		env_file_encoding="utf-8",
		case_sensitive=False,
	)

	embed_model: str = Field(
		default="TaylorAI/bge-micro", description="Hugging Face model id for embeddings"
	)
	default_metric: Literal["cosine", "dot", "euclidean"] = Field(
		default="cosine", description="Default distance metric"
	)
	index_dir: Path = Field(
		default_factory=lambda: _project_root() / "backend" / "index",
		description="Directory where the vector index is stored",
	)
	blog_json_path: Path = Field(
		default_factory=lambda: _project_root() / "blog.json",
		description="Path to blogs.json dataset",
	)
	cors_origins: List[str] = Field(
		default_factory=lambda: ["http://localhost:5173"],
		description="Allowed CORS origins",
	)
	batch_size: int = Field(default=64, ge=1, le=1024)
	device: Literal["auto", "cpu", "cuda", "mps"] = Field(default="auto", description="Unused in MVP; library default device is used.")
	max_seq_length: Optional[int] = Field(default=512, description="Max sequence length for encoder")
	normalize_input_text: bool = Field(default=True, description="Apply simple text normalization before encoding")


@lru_cache
def get_settings() -> Settings:
	s = Settings()
	s.index_dir.mkdir(parents=True, exist_ok=True)
	return s
