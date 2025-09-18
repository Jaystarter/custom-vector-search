PY=python3
PIP=pip3
VENV?=.venv

.PHONY: venv install dev index test lint fmt bench

venv:
	$(PY) -m venv $(VENV)
	$(VENV)/bin/$(PIP) install --upgrade pip

install: venv
	$(VENV)/bin/$(PIP) install -r backend/requirements.txt

dev:
	$(VENV)/bin/uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

index:
	$(VENV)/bin/$(PY) backend/scripts/reindex.py

bench:
	$(VENV)/bin/$(PY) backend/scripts/bench.py

test:
	$(VENV)/bin/pytest -q backend/tests

lint:
	$(VENV)/bin/ruff check backend
	$(VENV)/bin/mypy backend

fmt:
	$(VENV)/bin/isort backend
	$(VENV)/bin/black backend
