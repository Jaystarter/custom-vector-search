
## Front‑end

- Vite + React + TypeScript UI.
- Shows all posts by default:
  - On page load it calls `GET /posts` and renders every entry returned.
- Searching:
  - Sends `POST /search` with `{ query, k, metric }`.
  - Renders the results in the exact order returned (already sorted by similarity).
- Live controls:
  - Changing `metric` or `top‑k` immediately re‑runs the search if a query is present.
  - If the query is empty, the UI keeps showing the full list (`/posts`).
- Errors:
  - If the backend can’t load the model or index, the API returns `503`; the UI shows a toast with the message.

---

## Backend

- FastAPI app with three endpoints:
  - `GET /health` → `{ status: "ok" }`.
  - `GET /posts` → `{ results: [{ id, text, score: 0.0 }] }` (all items in the index, no ranking).
  - `POST /search` → `{ results: [{ id, text, score }] }` (ranked top‑k).

### Create embeddings (one‑time on first start or via reindex)

1. On service startup, the backend checks for an index at `backend/index/`:
   - files: `data.npz` and `index.json` (two‑file format).
2. If the files are missing:
   - Read `blog.json`.
   - Embed every post’s `metadata.text` using `TaylorAI/bge-micro` (no fallback).
   - Build an in‑memory flat index and persist:
     - `data.npz` → dense NumPy arrays used for search.
     - `index.json` → ids + metadatas + manifest.
3. If the files exist:
   - Skip embedding and just load the index into memory (fast path).

### Search (on every request)

1. Front‑end sends `POST /search` with `{ query, k, metric }`.
2. Backend embeds the query with `TaylorAI/bge-micro`.
3. The custom flat index computes similarity against in‑memory arrays and selects top‑k:
   - Metrics supported: cosine, dot, euclidean (L2).
   - Uses vectorized NumPy ops and `np.argpartition` for efficient top‑k.
4. Map row indices → `ids[i]` and `metadatas[i].text`, return ranked results.

---

## Storage

- Source data: `blog.json` (list of entries `{ id: string, metadata: { text: string } }`).

- Persisted index (two files, aligned by position):
  - `backend/index/data.npz` (NumPy)
    - `vectors` `(N, D) float32`: raw embeddings.
    - `normed` `(N, D) float32`: L2‑normalized copies (for cosine).
    - `sqnorms` `(N,) float32`: precomputed squared norms (for L2).
  - `backend/index/index.json` (JSON)
    - `ids: string[]` — the i‑th id matches row i in `data.npz`.
    - `metadatas: {text: string}[]` — the i‑th metadata matches row i.
    - `manifest: { version, dimension, model, default_metric, created_at }`.

- Positional alignment invariant:
  - Row `i` in `data.npz` ↔ `ids[i]` ↔ `metadatas[i]`.

---

## Notes
- Flat index = linear scan (exact top‑k) — simple, predictable, and correct for small/medium N.
- Reindexing: run the provided script to rebuild the files from `blog.json` when the dataset changes.