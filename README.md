# Auxilio Mecánico Backend

Backend API for a vehicle emergency assistance platform built with **FastAPI**, **SQLAlchemy 2.0 (async)**, and **PostgreSQL**.

## Tech Stack

- Python 3.12 · FastAPI · SQLAlchemy asyncio + asyncpg
- Alembic (migrations) · Pydantic Settings
- JWT auth (python-jose) · bcrypt passwords
- Docker & docker-compose · GitHub Actions CI

## Quick Start

```bash
# 1. Copy env file
cp .env.example .env

# 2. Start services
docker compose up -d

# 3. Run the SQL script to create the schema and tables
psql -h localhost -U postgres -d auxilio_mecanico -f db-script.sql

# 4. Access API docs
open http://localhost:8000/docs
```

## Local Development (without Docker)

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Migrations

```bash
# Generate a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Tests

```bash
pytest -v
```

## Project Structure

```
app/
├── api/          # FastAPI routers & dependencies
│   ├── deps.py
│   └── v1/
│       ├── api.py
│       └── endpoints/
├── core/         # Config, security, logging, exceptions
├── db/           # SQLAlchemy engine, session, seed data
├── middlewares/   # Request ID, error handler
├── models/       # SQLAlchemy ORM models (19 tables)
├── repositories/  # Data access layer (repository pattern)
├── schemas/      # Pydantic request/response schemas
├── services/     # Business logic layer
├── utils/        # Enums, datetime helpers
└── main.py       # App factory & lifespan
migrations/       # Alembic migrations
tests/            # pytest + httpx async tests
```

## Health Check

```
GET /api/v1/health → {"status": "ok"}
```
