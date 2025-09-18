# Custom Vector Search

Fast, simple text retrieval system with a custom flat vector database, FastAPI backend, and a polished Vite + React frontend.

## Stack
- Backend: FastAPI, custom NumPy flat index (cosine/dot/euclidean), Sentence-Transformers embeddings (BGE family)
- Frontend: Vite + React + TypeScript, Tailwind, minimal Radix (toast), framer-motion/lucide

## Prereqs
- Python 3.11
- Node 20+

## Setup & Run (dev)
```bash
# From project root
python3 -m venv .venv
./.venv/bin/pip install -U pip
./.venv/bin/pip install -r backend/requirements.txt

# Start backend
./.venv/bin/uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

# In another shell: start frontend
cd frontend
npm install
npm run dev -- --port 5173
```

Open http://localhost:5173

## Data
Place your dataset with the name `blog.json` with entries:
```json
[
  { "id": "uuid", "metadata": { "text": "..." } }
]
```

## Indexing
Index builds automatically on first backend start. Rebuild manually:
```bash
make -C backend index
```

## API
- POST `/search`
  - body: `{ "query": string, "k": number, "metric": "cosine|dot|euclidean" }`
  - response: `{ results: [{ id, text, score }] }`
- GET `/health`

## Notes
- Index format is two files: `backend/index/data.npz` (vectors) and `backend/index/index.json` (ids, metadatas, manifest).

## Testing & Linting
```bash
make -C backend test
make -C backend lint
make -C backend fmt
```
