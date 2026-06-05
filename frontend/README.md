# Citexis Frontend

React + TypeScript + Tailwind CSS UI for the Citexis academic paper discovery API.

## Prerequisites

- Node.js 20+
- Backend running at `http://localhost:8000`

## Setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

The dev server proxies `/api` requests to the FastAPI backend.

## Pages

| Route | Description |
|-------|-------------|
| `/` | Hybrid search with filters |
| `/papers/:id` | Paper detail, references, recommendations |
| `/explore?tag=...` | Topic clusters by venue |
| `/authors/:name` | Papers by author |

## Build

```bash
npm run build
npm run preview
```

## Environment

Optional `.env`:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

If unset, the app uses the Vite proxy (`/api/v1`).
