# Citexis

Hybrid academic paper discovery: **MongoDB** (metadata) + **Pinecone** (semantic search) + **Elasticsearch** (keyword), with a **React** frontend and **Celery + Redis** for background bulk imports.

## Architecture

### System overview

Citexis splits work across three stores and two runtimes:

| Store / runtime          | Role                                                          |
| ------------------------ | ------------------------------------------------------------- |
| **MongoDB**        | Canonical paper metadata, embedding status, user interactions |
| **Elasticsearch**  | BM25 keyword search over title/abstract                       |
| **Pinecone**       | Text records in `papers-abstract`; index embeds server-side |
| **FastAPI**        | HTTP API, JWT auth, dependency wiring, request handling       |
| **Celery + Redis** | Background ingestion and indexing (retries, bulk import)      |

```mermaid
flowchart TB
    subgraph clients [Clients]
        UI[Frontend / CLI]
    end

    subgraph api [FastAPI — app/]
        Routes[api/routes]
        Deps[api/deps — wire_app_state]
        Routes --> Deps
    end

    subgraph services [Domain services — app/services/]
        Ingest[ingestion/pipeline]
        Search[search/hybrid]
        Reco[recommendations/engine]
        Explore[explore/queries]
    end

    subgraph data [Data layer]
        Repo[repositories/]
        Mongo[(MongoDB)]
        ES[(Elasticsearch)]
        PC[(Pinecone)]
    end

    subgraph workers [Background — app/workers/]
        Celery[Celery tasks]
    end

    UI --> Routes
    Deps --> Ingest & Search & Reco & Explore
    Ingest --> Repo
    Search --> Repo
    Search --> ES
    Search --> PC
    Reco --> Repo
    Explore --> Mongo
    Repo --> Mongo
    Celery --> Ingest
    Celery -.-> Redis[(Redis broker)]
```

### Layered design

Requests flow **top-down**; each layer has a single responsibility so you can extend one concern without touching unrelated code.

```
HTTP request
    → api/routes/          # Thin handlers: validate input, call service, return schema
    → api/deps.py          # FastAPI Depends + app.state singletons (wired at startup)
    → services/            # Business logic (search, ingest, recommend, explore)
    → repositories/        # MongoDB queries only — no ES/Pinecone here
    → db/                  # Connection clients (Motor, AsyncElasticsearch, Pinecone)
```

| Layer                  | Path                  | Responsibility                                                      |
| ---------------------- | --------------------- | ------------------------------------------------------------------- |
| **Routes**       | `app/api/routes/`   | REST endpoints; use typed deps from `deps.py`                     |
| **Schemas**      | `app/core/schemas/` | Pydantic request/response models shared across API and workers      |
| **Services**     | `app/services/`     | Orchestration: multi-store workflows, algorithms                    |
| **Repositories** | `app/repositories/` | CRUD and queries against MongoDB collections                        |
| **DB clients**   | `app/db/`           | Lazy clients, index helpers, connection lifecycle                   |
| **Workers**      | `app/workers/`      | Celery tasks that reuse the same services as the API                |
| **Config**       | `app/config.py`     | `Settings` from `.env` — all fields required, no code defaults |

Startup wiring lives in `wire_app_state()` (`app/api/deps.py`): it builds repositories, indexers, `IngestionPipeline`, `HybridSearchService`, `RecommendationEngine`, and attaches them to `app.state` for the request lifetime.

### Data flows

**Ingestion** (sync for manual entry, or async via Celery for bulk imports):

```
Source (OpenAlex / Crossref DOI / JSON file + optional CORE full-text URL enrichment)
    → normalizer          # app/services/ingestion/normalizer.py
    → MongoDB create      # paper_repository (dedup by DOI when present)
    → Pinecone upsert_records  # embed title + abstract + tags (title-only if no abstract)
    → Elasticsearch index # elasticsearch_indexer
    → status = INDEXED    # embedding_status on paper doc
```

Import paths:

| Method               | Source              | Mode                        | Notes                                                                   |
| -------------------- | ------------------- | --------------------------- | ----------------------------------------------------------------------- |
| Multi-DOI bulk       | Crossref            | **Celery** (UI + API) | One or many DOIs; optional CORE `full_text_url` enrichment            |
| OpenAlex bulk        | OpenAlex            | **Celery** (UI + API) | Search by query; tags from keywords/concepts                            |
| JSON bulk            | User file           | **Celery** (UI + API) | Complete metadata in JSON;**no** CORE enrichment                  |
| Manual ingest        | User form           | **Sync** (UI + API)   | Blocks until MongoDB + both indexes are updated                         |
| arXiv search         | arXiv API           | Search only                 | Extract DOIs → import via multi-DOI bulk (Celery)                      |
| Single DOI / scripts | Crossref / OpenAlex | Sync or Celery              | `/import/doi/sync` and `/import/openalex/sync` for blocking API use |

**Background imports** queue a Celery task and return `task_id`. Poll `GET /api/v1/tasks/{task_id}` until `ready: true` for imported/skipped/failed counts. The Import page does this automatically for DOI, OpenAlex, and JSON bulk flows.

JSON bulk requires every paper to include `title`, `authors`, `abstract`, `year`, `venue`, `tags`, and `full_text_url`. See `fixtures/sample_papers.json`. Limits: `JSON_IMPORT_MAX_BYTES`, `JSON_IMPORT_MAX_PAPERS` in `.env`.

**Hybrid search**:

```
Query
    ├─ KeywordSearchService  → Elasticsearch (BM25, filters)
    └─ SemanticSearchService → Pinecone search + rerank in one call (optional)
            ↓
    reciprocal_rank_fusion (RRF)   # app/services/search/rrf.py
            ↓
    hydrate from MongoDB           # paper_repository.get_many_by_ids
            ↓
    SearchResponse
```

**Recommendations** (related papers):

```
paper_id
    ├─ ContentBasedRecommender    → Pinecone similarity
    ├─ CitationBasedRecommender   → MongoDB citation edges
    └─ CollaborativeRecommender   → user interaction history
            ↓
    weighted merge → RecommendationResponse
```

### Where to extend

| Goal                           | Start here                                                                                                                                       |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| New API endpoint               | `app/api/routes/` + register in `routes/__init__.py`; add a dep in `deps.py` or `auth_deps.py` if you need a new service                |
| Auth / access control          | `app/api/auth_deps.py`, `app/services/auth/service.py`, `app/api/routes/auth.py`                                                          |
| New paper source               | `app/services/ingestion/sources/` (implement `base.py`), call from a route or Celery task                                                    |
| arXiv DOI lookup               | `app/services/ingestion/sources/arxiv.py` + `GET /papers/import/arxiv/search`                                                                |
| Tune search                    | `app/config.py` (`search_*`, `pinecone_*`), `hybrid.py`, `rrf.py`                                                                      |
| New recommendation signal      | `app/services/recommendations/` + register weight in `engine.py`                                                                             |
| Explore / browse queries       | `app/services/explore/queries.py`                                                                                                              |
| Async long jobs                | `app/workers/tasks.py` — `ingest_json_bulk_task`, `ingest_dois_bulk_task`, `ingest_openalex_task`; poll via `app/api/routes/tasks.py` |
| ES index mapping               | `scripts/setup_es_index.py`                                                                                                                    |
| Reconcile indexes with MongoDB | `scripts/reindex_elasticsearch.py`, `scripts/reindex_pinecone.py`, `scripts/cleanup_orphan_indexes.py`                                     |

### Project layout

```
citexis/
├── frontend/                       # React UI (Vite + TypeScript + Tailwind)
│   └── src/
│       ├── api/client.ts           # API client (JWT bearer)
│       ├── context/AuthContext.tsx # Sign-in state + token storage
│       ├── components/             # Layout, SearchBar, PaperCard, PaperRating, ProtectedRoute, …
│       └── pages/                  # Home, Paper, Related, Explore, Saved, Import, Author, Login, Register
├── app/
│   ├── main.py                     # FastAPI app + lifespan (wire / teardown)
│   ├── config.py                   # Settings from .env
│   ├── api/
│   │   ├── deps.py                 # Dependency injection + wire_app_state
│   │   ├── auth_deps.py            # JWT deps: CurrentUserDep, AdminUserDep
│   │   └── routes/
│   │       ├── auth.py             # POST /auth/login, /register; GET /auth/me
│   │       ├── search.py           # POST /search (hybrid)
│   │       ├── papers.py           # CRUD, sync/async ingest, related (import/delete: admin)
│   │       ├── tasks.py            # GET /tasks/{id} — Celery task polling (admin)
│   │       ├── interactions.py     # saves, ratings, views, clicks (auth for writes)
│   │       ├── authors.py          # Author paper lists
│   │       └── explore.py          # Topic clusters, citation neighbors
│   ├── core/
│   │   ├── constants.py            # Enums (embedding status, user roles, …)
│   │   └── schemas/                # paper, search, user, auth, recommendation, arxiv, json_import, doi_import
│   ├── db/
│   │   ├── mongodb.py
│   │   ├── elasticsearch.py
│   │   └── pinecone_client.py
│   ├── repositories/
│   │   ├── paper_repository.py
│   │   ├── user_repository.py      # user_interactions collection
│   │   └── account_repository.py   # users collection (auth accounts)
│   ├── services/
│   │   ├── auth/
│   │   │   └── service.py          # JWT, bcrypt, bootstrap admin
│   │   ├── ingestion/
│   │   │   ├── pipeline.py         # ingest_one / ingest_many / index_paper
│   │   │   ├── json_import.py      # parse & validate bulk JSON uploads
│   │   │   ├── normalizer.py
│   │   │   └── sources/            # openalex, crossref, arxiv, core_enricher
│   │   ├── indexing/               # elasticsearch_indexer, pinecone_indexer, pinecone_text
│   │   ├── search/                 # keyword, semantic, pinecone_search, rrf, hybrid
│   │   ├── recommendations/        # content, citation, collaborative, engine
│   │   └── explore/                # tag clusters (MongoDB), author lists, citation DOIs
│   └── workers/
│       ├── celery_app.py
│       └── tasks.py                # bulk JSON/DOI/OpenAlex tasks, index_paper_task
├── fixtures/
│   └── sample_papers.json          # Example JSON bulk import file
├── scripts/
│   ├── setup_es_index.py           # Create ES index + auto-backfill (es-init)
│   ├── reindex_elasticsearch.py    # Mongo → ES backfill
│   ├── reindex_pinecone.py         # Mongo ↔ Pinecone audit + backfill
│   └── cleanup_orphan_indexes.py   # Remove ES/Pinecone rows with no Mongo doc
├── ruff.toml                       # Ruff lint/format configuration
├── .pre-commit-config.yaml         # Git hooks (Ruff + file hygiene)
├── requirements-dev.txt            # ruff, pre-commit
└── .env.example
```

## Quick start

### Option A — Docker (recommended)

MongoDB and Pinecone stay **external** (Atlas or host MongoDB + Pinecone API key).
Elasticsearch, Redis, API, worker, and frontend run via Docker Compose.

On **Linux**, services use **`network_mode: host`** so containers can reach Atlas/Pinecone and bind directly to host ports (Docker’s bridge DNS/port-proxy is unreliable on some setups).

```bash
# 1. Configure environment (all variables required — see .env.example)
cp .env.example .env
# Edit .env: MONGODB_URI, PINECONE_API_KEY, JWT_SECRET_KEY, AUTH_ADMIN_*, and remaining values

# 2. Stop any old Elasticsearch container using port 9200
docker stop elasticsearch 2>/dev/null || true

# 3. Start the full stack
docker compose up --build
```

| URL                        | Service                                                |
| -------------------------- | ------------------------------------------------------ |
| http://localhost:5173      | Frontend (Vite dev server)                             |
| http://localhost:8000/docs | API docs                                               |
| http://localhost:9200      | Elasticsearch                                          |
| localhost:6380 (default)   | Redis (see `REDIS_HOST_PORT` in `.env`)              |

**First sign-in:** set `AUTH_ADMIN_EMAIL` and `AUTH_ADMIN_PASSWORD` in `.env`. The API creates or updates that admin account on startup. Use it to access **Import** and paper **delete** in the UI.

Generate a strong JWT secret:

```bash
openssl rand -hex 32
```

**`.env` notes for Docker (host networking)**

Compose overrides `ELASTICSEARCH_URL` and `REDIS_URL` for `api` / `worker` / `es-init` to `127.0.0.1`. Your `.env` can keep local-dev values; what matters for MongoDB and external APIs:

| Variable | Docker recommendation |
| -------- | ----------------------- |
| `MONGODB_URI` | Prefer a **standard** `mongodb://…` Atlas URI with explicit shard hosts. Avoid `mongodb+srv://` if container DNS cannot resolve SRV records. |
| `JWT_SECRET_KEY` | Required — random hex string |
| `AUTH_ADMIN_EMAIL` / `AUTH_ADMIN_PASSWORD` | Bootstrap admin for import/delete |
| `REDIS_HOST_PORT` | Default `6380` — Redis listens on this host port |

If port **6380** is in use, set `REDIS_HOST_PORT=6381` (or any free port) in `.env` and restart Compose.

**Infra only** (run API/frontend on the host):

```bash
docker compose up elasticsearch redis es-init
```

Then set in `.env` for local processes:

```env
ELASTICSEARCH_URL=http://localhost:9200
REDIS_URL=redis://localhost:6380/0
MONGODB_URI=mongodb://localhost:27017
```

Use the same port as `REDIS_HOST_PORT` in `.env` (default **6380**).

**MongoDB**

| MongoDB location | `MONGODB_URI` in `.env` |
| ---------------- | ----------------------- |
| Atlas (Docker) | Standard `mongodb://user:pass@shard-host:27017,…/?ssl=true&replicaSet=…` (copy shard hosts from Atlas “standard connection string”) |
| Atlas (local API) | `mongodb+srv://…` or standard URI |
| MongoDB on host | `mongodb://localhost:27017` |

### Option B — Local Python + Node

```bash
# 1. Virtual env + deps
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
pip install -r requirements.txt
cp .env.example .env               # fill all values before starting

# 2. Start MongoDB locally; start Redis + Elasticsearch via Docker:
docker compose up elasticsearch redis es-init

# 3. Run API
uvicorn app.main:app --reload

# 4. Run Celery worker (required for DOI bulk, OpenAlex bulk, and JSON import on the Import page)
celery -A app.workers.celery_app worker --loglevel=info

# 5. Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

API docs: http://localhost:8000/docs

### Code quality (Ruff + pre-commit)

Same setup as the bundled `dSTORMQuant` reference project. Configuration lives in `ruff.toml`.

```bash
pip install -r requirements-dev.txt
# or: pip install -e ".[dev]"

ruff check .
ruff check . --fix

pre-commit install
pre-commit run --all-files
```

CI runs `ruff check .` on every push/PR (`.github/workflows/ci.yml`).

## Frontend

React UI in `frontend/` (Vite + TypeScript + Tailwind). Nav: **Search**, **Explore**, **Saved** (signed in), **Import** (admin).

| Route                   | Features                                                                                       | API                                                                                                                                                                               |
| ----------------------- | ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/`                   | Hybrid search with filters; indexed corpus count; click tracking on results                    | `GET /papers/stats`, `POST /search`, `POST /interactions/clicks/{id}` (signed in)                                                                                           |
| `/login`, `/register` | Sign in / create account                                                                       | `POST /auth/login`, `POST /auth/register`                                                                                                                                       |
| `/papers/:id`         | Detail, references, related preview, save/unsave (signed in), rating (signed in), delete (admin) | `GET /papers/{id}`, `GET /explore/papers/{id}/neighbors`, `POST /interactions`, `DELETE /papers/{id}`                                                                     |
| `/papers/:id/related` | Full related-papers list                                                                       | `GET /papers/{id}/related`                                                                                                                                                      |
| `/explore?tag=…`     | Papers grouped by matching tags (MongoDB; partial tag match)                                   | `GET /explore/topics`                                                                                                                                                           |
| `/saved`              | Saved papers list, unsave (signed in)                                                          | `GET /interactions/me/saved`, `DELETE /interactions/me/saved/{paper_id}`                                                                                                     |
| `/import`             | Multi-DOI, OpenAlex bulk, JSON upload (background), arXiv DOI extraction, manual ingest (admin) | `POST /papers/import/doi/bulk`, `POST /papers/import/openalex`, `POST /papers/import/json`, `GET /tasks/{id}`, `GET /papers/import/arxiv/search`, `POST /papers/sync` |
| `/authors/:name`      | Papers by author; click tracking (signed in)                                                   | `GET /authors/{name}/papers`, `POST /interactions/clicks/{id}`                                                                                                                |

**Authentication:** JWT bearer tokens stored in the browser. Search and read endpoints are public; saves/ratings require sign-in; import/delete/task polling require an **admin** account. The frontend sends `Authorization: Bearer <token>` on API calls after login.

**With Docker** (included in `docker compose up`): http://localhost:5173

**Locally:**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — API calls are proxied to the backend.

See [frontend/README.md](frontend/README.md) for build and env details.

## API

Base path: `/api/v1`. Interactive docs: http://localhost:8000/docs

### Search & browse

| Method | Path                               | Description                               | UI                      |
| ------ | ---------------------------------- | ----------------------------------------- | ----------------------- |
| POST   | `/search`                        | Hybrid search (ES + Pinecone + RRF)       | Home page               |
| GET    | `/papers/stats`                  | Total papers in MongoDB corpus            | Home page               |
| GET    | `/papers/{id}`                   | Paper detail + top recommendations        | Paper page              |
| GET    | `/papers/{id}/related`           | Blended recommendations                   | Related page            |
| DELETE | `/papers/{id}`                   | Delete paper from MongoDB + ES + Pinecone (**admin**) | Paper page              |
| GET    | `/authors/{name}/papers`         | Author paper list                         | Author page             |
| GET    | `/explore/topics?tag=…`         | Papers with similar tags, grouped by tag  | Explore page            |
| GET    | `/explore/papers/{id}/neighbors` | Citation DOI neighbors                    | Paper page (references) |

### Import (sync — manual entry only, **admin**)

| Method | Path             | Description                                | UI          |
| ------ | ---------------- | ------------------------------------------ | ----------- |
| POST   | `/papers/sync` | Manual paper ingest (blocks until indexed) | Import page |

Sync import endpoints for scripts (**admin**, not used by the Import page UI):

| Method | Path                             | Description                                            |
| ------ | -------------------------------- | ------------------------------------------------------ |
| POST   | `/papers/import/doi/sync`      | Single DOI via Crossref (+ OpenAlex abstract fallback) |
| POST   | `/papers/import/openalex/sync` | OpenAlex search import (blocks until done)             |

### Import (async — Celery, **admin**, used by UI for bulk flows)

| Method | Path                            | Description                                 | UI                            |
| ------ | ------------------------------- | ------------------------------------------- | ----------------------------- |
| POST   | `/papers/import/doi/bulk`     | Multi-DOI import (`{ dois, enrich }`)     | Import page, arXiv DOI import |
| POST   | `/papers/import/openalex`     | OpenAlex bulk import (query + limit)        | Import page                   |
| POST   | `/papers/import/json`         | JSON file upload (multipart)                | Import page                   |
| GET    | `/papers/import/arxiv/search` | Search arXiv and extract DOIs               | Import page                   |
| POST   | `/papers`                     | Queue manual paper ingest                   | —                            |
| POST   | `/papers/import/doi`          | Queue single DOI ingest                     | —                            |
| POST   | `/papers/import/{source}`     | Generic import (`openalex`, `crossref`) | —                            |

Poll task status after any `202 Accepted` import:

| Method | Path                 | Description                         | UI                      |
| ------ | -------------------- | ----------------------------------- | ----------------------- |
| GET    | `/tasks/{task_id}` | Celery state + result when complete (**admin**) | Import page (auto-poll) |

Requires the **worker** (`celery -A app.workers.celery_app worker` or the `worker` Compose service).

### Explore topics

Explore uses **MongoDB only** (not Pinecone or Elasticsearch):

1. User enters a topic string (e.g. `learning`).
2. Papers are matched where any **tag** contains that string (case-insensitive).
3. Results are **grouped by tag** (e.g. `machine learning`, `deep learning`).
4. All papers in each tag group are listed with links to paper detail.

Tags are populated on **OpenAlex** import (keywords/concepts) or **manual** ingest. Crossref DOI imports usually have empty tags unless added manually.

### Interactions (authenticated)

| Method | Path                                                       | Description                                         | UI                               |
| ------ | ---------------------------------------------------------- | --------------------------------------------------- | -------------------------------- |
| POST   | `/interactions`                                          | Record `save` or `rating` (signed in)        | Paper page                       |
| POST   | `/interactions/views/{paper_id}`                         | Record `view` (signed in; no-op if anonymous) | Paper page                       |
| POST   | `/interactions/clicks/{paper_id}`                        | Record `click` (signed in; no-op if anonymous) | Search/author/explore clicks     |
| GET    | `/interactions/me/saved`                                 | List saved paper IDs                                | Saved page                       |
| DELETE | `/interactions/me/saved/{paper_id}`                      | Remove save                                         | Saved page, Paper page           |
| GET    | `/interactions/me/papers/{paper_id}/rating`              | User rating for a paper                             | Paper page                       |

### Auth

| Method | Path              | Description              |
| ------ | ----------------- | ------------------------ |
| POST   | `/auth/register`  | Create account + JWT     |
| POST   | `/auth/login`     | Sign in + JWT            |
| GET    | `/auth/me`        | Current user (Bearer)    |

## Tech choices (defaults)

| Component      | Default                                                              |
| -------------- | -------------------------------------------------------------------- |
| Auth           | JWT (HS256) + bcrypt; bootstrap admin from `.env`                    |
| Pinecone embed | Index-configured hosted model (server-side)                          |
| Queue          | Celery + Redis (required for bulk imports on the Import page)        |
| Keyword search | Elasticsearch (Docker)                                               |
| Metadata       | MongoDB (external)                                                   |
| API            | FastAPI (Docker or local)                                            |
| Vector DB      | Pinecone namespace `papers-abstract` (text records + server embed) |

## Docker layout

All services use **`network_mode: host`** on Linux so they bind directly to host ports and use the host’s DNS (required for MongoDB Atlas and Pinecone from containers).

```
docker compose up
├── elasticsearch   → host :9200 (volume es_data)
├── redis           → host :6380 by default (volume redis_data; port from REDIS_HOST_PORT)
├── es-init         → one-shot: creates ES index; backfills if ES is behind MongoDB
├── api             → host :8000
├── worker          → Celery consumer (same Redis/ES/Mongo as api)
└── frontend        → host :5173 (Vite proxies /api → http://127.0.0.1:8000)
```

MongoDB and Pinecone are **not** in Compose — configure them in `.env`.

### Docker troubleshooting (Linux)

If containers cannot resolve external hostnames or published ports hang when accessed from the browser:

1. Ensure you are using **http://localhost:5173** and **http://localhost:8000** (not `172.x.x.x` addresses from container logs).
2. Prefer a **standard** `mongodb://` Atlas URI over `mongodb+srv://` when running in Docker.
3. Optionally fix Docker daemon DNS permanently in `/etc/docker/daemon.json`:

```json
{
  "dns": ["8.8.8.8", "1.1.1.1"]
}
```

Then restart Docker. The Compose file already uses host networking as the primary workaround.

## Maintenance scripts

Run from the project root via Docker (recommended) or locally with the same `.env`:

```bash
docker compose run --rm api python -m scripts.<script>
```

### Re-index Elasticsearch

On `docker compose up`, **es-init** automatically backfills Elasticsearch when the index is new or has fewer documents than MongoDB. Use the script below to audit or force a full re-index:

```bash
docker compose run --rm api python -m scripts.reindex_elasticsearch          # dry-run
docker compose run --rm api python -m scripts.reindex_elasticsearch --apply
```

### Audit / backfill Pinecone (Mongo ↔ vectors out of sync)

After failed ingests or manual MongoDB edits, verify every paper exists in Pinecone:

```bash
docker compose run --rm api python -m scripts.reindex_pinecone               # audit (exits 1 if out of sync)
docker compose run --rm api python -m scripts.reindex_pinecone --apply       # upsert missing + fix stale status
docker compose run --rm api python -m scripts.reindex_pinecone --apply --all # re-upsert every paper
```

Reports missing Pinecone IDs, `embedding_status` breakdown, and papers present in Pinecone but not marked `indexed` in Mongo.

### Clean orphaned index records (no Mongo doc)

Removes Elasticsearch and Pinecone entries whose IDs are not in MongoDB:

```bash
docker compose run --rm api python -m scripts.cleanup_orphan_indexes          # dry-run
docker compose run --rm api python -m scripts.cleanup_orphan_indexes --apply
```

## License

See [LICENSE](LICENSE).
