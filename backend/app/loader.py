from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def load_blogs(path: Path) -> List[Dict]:
	"""Load blog entries from JSON file.

	Each entry must have keys: id (str), metadata (dict with key 'text').
	"""
	with path.open("r", encoding="utf-8") as f:
		data = json.load(f)
	if not isinstance(data, list):
		raise ValueError("blogs.json must be a list of entries")
	entries: List[Dict] = []
	for i, item in enumerate(data):
		if not isinstance(item, dict):
			continue
		id_ = item.get("id")
		meta = item.get("metadata", {}) or {}
		text = meta.get("text")
		if not id_ or not isinstance(id_, str):
			continue
		if not text or not isinstance(text, str):
			continue
		entries.append({"id": id_, "metadata": {"text": text}})
	return entries
