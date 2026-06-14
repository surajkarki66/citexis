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
| `/` | Hybrid search with year/tag/venue filters; shows total indexed paper count |
| `/papers/:id` | Paper detail, references, related preview, save, rating, delete |
| `/papers/:id/related` | Full related-papers list |
| `/explore?tag=…` | Find papers by similar tags; grouped by tag with links to each paper |
| `/saved` | Saved papers (browser-local user ID) |
| `/import` | Multi-DOI bulk, OpenAlex bulk, JSON upload, arXiv DOI extraction, manual ingest | See **Import page** below |
| `/authors/:name` | Papers by author name |

### Import page

| Section | Behavior |
|---------|----------|
| **Import by DOI** | One or more DOIs → queued Celery task → poll until indexed |
| **Import from OpenAlex** | Search query + limit → background bulk import |
| **Extract DOIs from arXiv** | Search arXiv → list DOIs → copy, add to DOI field, or bulk import |
| **Bulk import from JSON** | Upload JSON with complete paper records → background import |
| **Manual paper ingest** | Fill form → sync index (blocks until done) |

Bulk imports (DOI, OpenAlex, JSON) require the **Celery worker** running. The page polls `GET /api/v1/tasks/{task_id}` until each job finishes.

JSON papers must include `title`, `authors`, `abstract`, `year`, `venue`, `tags`, and `full_text_url`. Sample: `fixtures/sample_papers.json` in the repo root.

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
