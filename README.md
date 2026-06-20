# Stockplane

A full-stack inventory and order management app for small businesses.

## Approach

The solution is split into a **FastAPI backend** and a **React SPA**, scoped around multi-tenant businesses. Registration creates a user and their first business; all catalog, inventory, customer, and order data is isolated by `business_id`.

**Backend** follows a layered design: routes → services → repositories → SQLAlchemy models. Business rules live in services — for example, orders move through a defined status lifecycle (draft → pending → confirmed → shipped → delivered), inventory is adjusted with row-level locking when orders are placed or cancelled, and mutating endpoints support **idempotency keys** to safely retry requests. Alembic manages schema migrations; pytest covers auth, products, inventory, orders, stats, and idempotency.

**Frontend** is a client-rendered app with file-based routing (TanStack Router), server-state caching (TanStack Query), form validation (React Hook Form + Zod), and a shared shell for navigation across products, inventory, customers, orders, and a dashboard with business stats.

**Deployment** is containerised: PostgreSQL, the API, and an nginx-served frontend build are wired together with Docker Compose and a root `.env` file.

## Stack

| Layer | Technologies |
| ----- | ------------ |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2 (async), Alembic, PostgreSQL, Pydantic, JWT auth |
| Frontend | React 19, Vite, TanStack Router & Query, Tailwind CSS, shadcn-style UI components, Axios |
| Tooling | Docker, Docker Compose, pytest, ESLint |

## Docker Hub

The production backend image is published on Docker Hub:

- [syedtazy/stockplane-backend](https://hub.docker.com/r/syedtazy/stockplane-backend)

```bash
docker pull syedtazy/stockplane-backend:latest
```

## Run with Docker Compose

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/)

### Quick start

1. Copy the environment file and review the values:

   ```bash
   cp .env.example .env
   ```

2. Start all services:

   ```bash
   docker compose up --build
   ```

3. Open the app:

   - Frontend: [http://localhost:5173](http://localhost:5173)
   - API: [http://localhost:8000/api](http://localhost:8000/api)
   - Health check: [http://localhost:8000/health](http://localhost:8000/health)

The backend runs database migrations automatically on startup.

### Services

| Service  | Description              | Default port |
| -------- | ------------------------ | ------------ |
| `db`     | PostgreSQL 16            | internal     |
| `backend`| FastAPI API              | 8000         |
| `frontend` | React app (nginx)      | 5173         |

### Environment variables

All Compose settings live in `.env` at the repo root. See [.env.example](.env.example) for the full list.

Important notes:

- `VITE_API_URL` is embedded in the frontend at **build time**. If you change it, rebuild the frontend:

  ```bash
  docker compose up --build frontend
  ```

- `CORS_ORIGINS` must include the URL you use to open the frontend in your browser.

- Set a strong `SECRET_KEY` before deploying anywhere other than local development.

### Useful commands

```bash
# Run in the background
docker compose up -d --build

# View logs
docker compose logs -f

# Stop and remove containers
docker compose down

# Stop and remove containers plus the database volume
docker compose down -v
```

## Local development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install ".[dev]"
cp ../.env.example .env   # set DATABASE_URL to your local Postgres
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
VITE_API_URL=http://localhost:8000/api npm run dev
```

The Vite dev server runs at [http://localhost:5173](http://localhost:5173) by default.

## Project structure

```
.
├── backend/          # FastAPI API, SQLAlchemy models, Alembic migrations
├── frontend/         # React + Vite SPA
├── docker-compose.yml
└── .env.example
```
