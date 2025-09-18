from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


Metric = Literal["cosine", "dot", "euclidean"]


class SearchRequest(BaseModel):
	query: str = Field(min_length=1)
	k: int = Field(default=10, ge=1, le=100)
	metric: Optional[Metric] = None
	normalize: Optional[bool] = False

	@field_validator("query")
	@classmethod
	def strip_query(cls, v: str) -> str:
		return v.strip()


class SearchHit(BaseModel):
	id: str
	text: str
	score: float


class SearchResponse(BaseModel):
	results: list[SearchHit]


class HealthResponse(BaseModel):
	status: str = "ok"
