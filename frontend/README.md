# Citexis Frontend

React + TypeScript + Tailwind CSS UI for the Citexis academic paper discovery API.

## With Docker

From the project root:

```bash
docker compose up --build
```

Open http://localhost:5173

## Local development

### Prerequisites

- Node.js 20+
- Backend running at `http://localhost:8000`

### Setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

The dev server proxies `/api` requests to the FastAPI backend.

When the frontend runs inside Docker, `VITE_PROXY_TARGET=http://api:8000` is set automatically.

## Pages

| Route | Description |
|-------|-------------|
| `/` | Hybrid search with year/tag/venue filters |
| `/papers/:id` | Paper detail, references, related preview, save, rating, delete |
| `/papers/:id/related` | Full related-papers list |
| `/explore?tag=…` | Topic clusters grouped by venue |
| `/saved` | Saved papers (browser-local user ID) |
| `/import` | Sync import: DOI, OpenAlex search, manual paper form |
| `/authors/:name` | Papers by author name |

All imports run synchronously — the UI waits for MongoDB + Elasticsearch + Pinecone indexing to finish.

## Build

```bash
npm run build
npm run preview
```

## Environment

Optional `.env`:

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_PROXY_TARGET=http://localhost:8000
```

If `VITE_API_URL` is unset, the app uses the Vite proxy (`/api/v1`).
