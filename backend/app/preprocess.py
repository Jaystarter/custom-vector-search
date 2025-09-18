from __future__ import annotations

import re

_whitespace_re = re.compile(r"\s+")


def normalize_text(text: str) -> str:
	# Lowercase and collapse whitespace; strip ends
	return _whitespace_re.sub(" ", text).strip().lower()
