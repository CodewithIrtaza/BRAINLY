# Brainly — AI Customer Support Agent Platform

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Brainly is a no-code AI customer support platform where businesses upload their data (PDFs, FAQs, URLs) to create a custom agent that answers questions 24/7 on their website.

## Current Status

**Phase:** Project Scaffold Complete ✅
**Implementation:** FastAPI backend with SQLAlchemy 2.0, pgvector, and Supabase integration
**Next:** Implement RAG pipeline, authentication, and dashboard frontend

## Architecture

```
brainly/
├── apps/
│   ├── api/           # FastAPI Backend (Python 3.11+)
│   │   ├── src/
│   │   │   ├── main.py           # App factory & entry point
│   │   │   ├── config.py         # Pydantic Settings
│   │   │   ├── database.py       # SQLAlchemy async engine
│   │   │   ├── models/           # SQLAlchemy models
│   │   │   ├── schemas/          # Pydantic request/response
│   │   │   ├── api/v1/           # API routes
│   │   │   ├── services/         # Business logic (LLM, RAG, embeddings)
│   │   │   ├── workers/          # Vercel Edge Functions
│   │   │   ├── utils/            # PDF, chunking, validators
│   │   │   └── exceptions/       # Custom exceptions
│   │   ├── tests/                # pytest tests
│   │   ├── alembic/              # Database migrations
│   │   ├── requirements.txt      # Production deps
│   │   └── requirements-dev.txt  # Dev deps
│   ├── web/           # Next.js Dashboard (TODO)
│   └── widget/        # Embeddable Chat Widget (TODO)
├── packages/shared-types/  # Shared TS/Python types (TODO)
├── docs/                   # PRD, TECH_DESIGN, API docs
└── .github/workflows/      # CI/CD pipelines
```

## Prerequisites

- **Python 3.11+** (3.12 recommended)
- **Supabase account** for PostgreSQL + pgvector + Auth + Storage
- **NVIDIA NIM API key** (primary LLM) — free tier available
- **Groq API key** (fallback LLM) — free tier available
- **Jina AI API key** (embeddings) — free tier available
- **Resend API key** (email) — free tier available

## Quick Start

### 1. Clone and Setup

```powershell
cd E:\BRAINLY

# Create virtual environment (if not exists)
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install production dependencies
pip install -r apps/api/requirements.txt

# Install development dependencies
pip install -r apps/api/requirements-dev.txt
```

### 2. Configure Environment

```powershell
# Copy example environment file
copy .env.example .env

# Edit .env with your API keys
notepad .env
```

Required variables to set:
- `DATABASE_URL` — Supabase PostgreSQL connection string
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`
- `NVIDIA_NIM_API_KEY` — from https://build.nvidia.com/
- `GROQ_API_KEY` — from https://console.groq.com/
- `JINA_AI_API_KEY` — from https://jina.ai/
- `RESEND_API_KEY` — from https://resend.com/

### 3. Run Database Migrations

```powershell
cd apps/api
alembic upgrade head
```

### 4. Start Development Server

```powershell
# From E:\BRAINLY\apps\api
python -m src.main
```

Or with uvicorn directly:
```powershell
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Verify Installation

Open your browser:
- **Health Check:** http://localhost:8000/health
- **API Docs:** http://localhost:8000/docs
- **Hello World:** http://localhost:8000/api/v1/health

Expected response:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

## Running Tests

```powershell
cd apps/api

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_health.py -v
```

## Linting & Type Checking

```powershell
cd apps/api

# Lint with Ruff
ruff check src/

# Format with Ruff
ruff format src/

# Type check with MyPy
mypy src/
```

## Project Structure Details

### Backend (apps/api)

| Module | Purpose |
|--------|---------|
| `src/main.py` | FastAPI app factory, lifespan, routers |
| `src/config.py` | Pydantic Settings from environment |
| `src/database.py` | SQLAlchemy async engine, sessions |
| `src/models/` | SQLAlchemy ORM models (Workspace, KB, Chat, Leads) |
| `src/schemas/` | Pydantic request/response validation |
| `src/api/v1/` | REST API endpoints |
| `src/services/` | LLM, Embeddings, RAG, Language detection |
| `src/workers/` | Vercel Edge Functions for background jobs |
| `src/utils/` | PDF extraction, text chunking, validators |

### Key Technologies

- **FastAPI** — Async web framework with OpenAPI
- **SQLAlchemy 2.0** — Async ORM with pgvector support
- **Supabase** — PostgreSQL, Auth, Realtime, Storage
- **pgvector** — Vector similarity search
- **NVIDIA NIM** — Llama 3.1 70B (primary LLM)
- **Groq** — Llama 3.1 70B (fallback LLM)
- **Jina AI v3** — Multilingual embeddings (1024-dim)
- **PyMuPDF + pdfplumber** — PDF text/table extraction
- **tiktoken** — Token counting

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/health` | API health check |
| POST | `/api/v1/auth/signup` | Create workspace (after Supabase signup) |
| GET | `/api/v1/workspaces` | List user workspaces |
| POST | `/api/v1/workspaces` | Create workspace |
| GET | `/api/v1/workspaces/{id}/agent` | Get agent config |
| PATCH | `/api/v1/workspaces/{id}/agent` | Update agent config |
| GET | `/api/v1/kb/sources` | List KB sources |
| POST | `/api/v1/kb/sources` | Create KB source |
| POST | `/api/v1/kb/sources/upload` | Upload PDF/TXT |
| POST | `/api/v1/chat/message` | Send chat message (widget) |
| POST | `/api/v1/chat/escalate` | Request human escalation |
| POST | `/api/v1/chat/lead` | Capture lead |
| GET | `/api/v1/analytics/overview` | Dashboard analytics |
| GET | `/api/v1/faq/suggestions` | List FAQ suggestions |

## Development Workflow

1. **Before any task:** Read `docs/STATUS.md` and `docs/TASKS.md`
2. **Write tests first** for new functionality
3. **Run tests** during development: `pytest tests/ -v`
4. **Run lint** before committing: `ruff check src/ && mypy src/`
5. **After completing task:** Update `docs/STATUS.md` and `docs/TASKS.md`
6. **Commit** with Conventional Commit message

## Deployment

### Vercel (Frontend + API)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy preview
vercel

# Deploy production
vercel --prod
```

### Supabase

1. Create project at https://supabase.com
2. Enable pgvector extension
3. Run migrations: `alembic upgrade head`
4. Configure Auth providers (Email, OAuth)
5. Set up Storage bucket for KB files

## Documentation

- `docs/PRD.md` — Product Requirements Document
- `docs/TECH_DESIGN.md` — Technical Design & Architecture
- `docs/STATUS.md` — Project Status (updated each session)
- `docs/TASKS.md` — Task Tracking (updated each session)

## License

MIT License — see [LICENSE](LICENSE) for details.