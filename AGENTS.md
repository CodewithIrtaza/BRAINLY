# AGENTS.md

## Essential Commands

| Task | Command | Working Directory |
|------|---------|-------------------|
| Install Python deps | `pip install -r requirements.txt` | `apps/api/` |
| Install dev deps | `pip install -r requirements-dev.txt` | `apps/api/` |
| Run dev server | Not configured | — |
| Run tests | Not configured | — |
| Run lint | Not configured | — |
| Format code | Not configured | — |
| Production build | Not configured | — |

> Frontend/widget projects don't exist yet.

## Non-Obvious Conventions

- **Root:** `E:\BRAINLY` — monorepo
- **Backend only:** `apps/api/` (FastAPI, SQLAlchemy 2.0, pgvector)
- **Multi-tenancy:** Supabase RLS — `workspace_id` from JWT claim
- **LLM:** NVIDIA NIM (primary) + Groq (fallback) via OpenAI client; Jina AI for embeddings
- **Async everywhere:** FastAPI, SQLAlchemy, httpx
- **Vector dims:** 1024 (Jina v3) — `VECTOR(1024)`
- **Languages:** `en`, `ur`, `ur-Roman` — detect before LLM call

## Testing Rules

- Write failing test first for bugs.
- Add tests for new functionality.
- Never weaken tests to pass.
- Run tests + lint before declaring complete.

## Git Rules

- Small, focused commits; Conventional Commits.
- Never commit secrets, `.env`, credentials.
- No history rewrites without permission.

## Dependency Management

- **Never add/remove/upgrade without approval.**
- Provide exact name + justification.
- Verify PyPI/npm, maintenance, compatibility.
- Prefer existing deps and stdlib.

## Never

- Hardcode secrets; bypass auth/RLS; overengineer.
- Silently change API contracts; modify unrelated files.
- Claim tests passed without running them.

## Mandatory Workflow

**Before task:** Read `docs/STATUS.md` → `docs/TASKS.md` → review docs/code → confirm scope.

**After task:** Run tests → full suite → lint → update `docs/STATUS.md` → tick `docs/TASKS.md` → Conventional Commit.
If checks fail — report, don't claim completion.