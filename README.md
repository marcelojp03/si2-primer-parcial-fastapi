# AuxilioMecánico — API

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg)](https://python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.x_async-D71F00.svg)](https://sqlalchemy.org/)
[![JWT](https://img.shields.io/badge/Auth-JWT-000000.svg)](https://jwt.io/)
[![OpenAI](https://img.shields.io/badge/OpenAI-Whisper+GPT-412991.svg)](https://openai.com/)
[![WebSocket](https://img.shields.io/badge/WebSocket-realtime-brightgreen.svg)](#)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Backend API for an intelligent vehicle emergency assistance platform. Connects clients in roadside emergencies with nearby workshops through AI-powered incident analysis and a smart multi-tenant assignment engine.

---

## Overview

The platform handles the full lifecycle of a roadside emergency:

- Clients submit incidents via mobile app — photos, audio and GPS location
- AI analyzes the evidence: **OpenAI Whisper** for audio transcription, **GPT-4o-mini** for image classification
- The assignment engine finds the best available workshop using distance (Haversine formula), specialties and reputation score
- Real-time updates delivered through **WebSocket** (in-app) and **Firebase Cloud Messaging** (push)
- Multi-tenant SaaS: each workshop group operates in an isolated tenant

---

## Tech Stack

| Category | Technology |
|----------|------------|
| **Framework** | FastAPI 0.111 |
| **Language** | Python 3.11 |
| **ORM** | SQLAlchemy 2.x async + asyncpg |
| **Database** | PostgreSQL 16 (schema `auxilio_mecanico`) |
| **Auth** | JWT — python-jose + bcrypt |
| **AI** | OpenAI Whisper (audio) · GPT-4o-mini (vision) |
| **Storage** | AWS S3 |
| **Real-time** | WebSocket (in-app) · Firebase Cloud Messaging (push) |
| **Containerization** | Docker + docker-compose |
| **Testing** | pytest + httpx (async) |

---

## Prerequisites

- Python 3.11+
- PostgreSQL 16 running locally or via Docker
- AWS S3 bucket
- Firebase project + service account JSON

---

## Setup

### 1. Clone and create virtual environment

```bash
git clone https://github.com/marcelojp03/si2-primer-parcial-fastapi.git
cd si2-primer-parcial-fastapi

python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -e ".[dev]"
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in the values:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/auxilio_mecanico
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=sk-...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=...
FIREBASE_CREDENTIALS_PATH=auxilio-mecanico-firebase.json
```

### 3. Initialize the database

```bash
# Create schema and tables
python scripts/db/create_tables.py

# Apply incremental SQL updates
psql -U postgres -d auxilio_mecanico -f scripts/db/001_multitenant_invitations.sql
psql -U postgres -d auxilio_mecanico -f scripts/db/002_tracking_sla.sql
```

### 4. Run the server

```bash
uvicorn app.main:app --reload --port 8000
```

API docs → `http://localhost:8000/docs`

---

## Docker

```bash
docker-compose up --build
```

---

## Tests

```bash
pytest tests/ -v
```

---

## Project Structure

```
app/
├── api/
│   ├── deps.py             # Auth guards & injected dependencies
│   └── v1/endpoints/       # Route handlers per feature
├── core/                   # Config, security, exceptions, logging
├── db/                     # SQLAlchemy session factory & init
├── middlewares/            # Request ID, global error handler
├── models/                 # SQLAlchemy ORM models
├── repositories/           # Data access layer (repository pattern)
├── schemas/                # Pydantic request/response schemas
├── services/               # Business logic layer
├── utils/                  # Enums, helpers
├── ws/                     # WebSocket module (manager, router, auth)
└── main.py                 # App factory
scripts/
└── db/                     # SQL migration scripts
tests/                      # pytest + httpx async test suite
```

---

## API

Base URL: `http://localhost:8000/api/v1/`

All endpoints require `Authorization: Bearer <token>` except `/auth/login` and `/auth/register`.

```
GET  /api/v1/health           → service health check
POST /api/v1/auth/login       → obtain JWT token
POST /api/v1/auth/register    → register new user
GET  /ws?token=<jwt>          → WebSocket connection
```

---

## Related

| Repository | Description |
|------------|-------------|
| [si2-primer-parcial-angular](https://github.com/marcelojp03/si2-primer-parcial-angular) | Angular admin dashboard |
| [si2-primer-parcial-flutter](https://github.com/marcelojp03/si2-primer-parcial-flutter) | Flutter mobile app |
