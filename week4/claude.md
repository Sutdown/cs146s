# Claude.md — Week 4 Autonomous Coding Agent Guide

> Guide for Claude Code agents working in the week4 project environment.

## Project Overview

**Week 4**: Build automations within a minimal full-stack "developer's command center" using Claude Code features (custom commands, SubAgents, MCP servers, and CLAUDE.md guidance).

**Tech Stack:**
- Backend: FastAPI + SQLAlchemy ORM + SQLite
- Frontend: Static HTML/CSS/JavaScript (no build step)
- Testing: pytest with isolated in-memory test DB
- Code Quality: Black + Ruff (enforced via pre-commit)

## Quick Start for Agents

### Essential Commands
```bash
# Terminal setup (required for Python imports)
set PYTHONPATH=.

# Build & Test
make run      # Start dev server on :8000 (with reload)
make test     # Run pytest -q backend/tests
make format   # Auto-format code (black + ruff --fix)
make lint     # Check code quality (ruff check)
make seed     # Seed DB from data/seed.sql
```

### Development Environment
- **Python Environment**: Conda (cs146s)
- **Entry Point**: `backend/app/main.py` (FastAPI application)
- **Database**: Auto-created and seeded on app startup
- **Static Files**: Served from `/static` path, index.html at root

## Architecture & Key Patterns

### File Organization
```
backend/
  app/
    main.py          # FastAPI app setup, startup events
    models.py        # SQLAlchemy ORM models (Note, ActionItem)
    schemas.py       # Pydantic request/response schemas
    db.py            # Database session management (get_db)
    routers/
      notes.py       # Note endpoints (CRUD)
      action_items.py # Action item endpoints
    services/
      extract.py     # Business logic (text extraction, tagging)
  tests/
    conftest.py      # Pytest fixtures (client fixture with temp in-memory SQLite)
    test_*.py        # Unit & integration tests
data/
  seed.sql           # SQLite schema + sample data (applied on first startup)
docs/
  TASKS.md           # 7 workflow areas ready for automation
frontend/            # Static HTML/CSS/JS (served by FastAPI)
```

### Core Design Patterns

| Pattern | Implementation | Notes |
|---------|----------------|-------|
| **Dependency Injection** | `Depends(get_db)` in route parameters | FastAPI pattern for test isolation |
| **ORM** | SQLAlchemy with `SessionLocal` | Auto-commit disabled; explicit `.commit()` required |
| **Schemas** | Pydantic with ORM mode (`model_config = ConfigDict(from_attributes=True)`) | Separate Create/Read variants |
| **Error Handling** | `HTTPException(status_code=404)` for missing records | Use appropriate HTTP codes |
| **Testing** | TestClient + temp in-memory SQLite per test | No shared test state |

## Development Conventions

### Code Style
- **Formatter**: Black (line length: default 88)
- **Linter**: Ruff (enforced via pre-commit hooks)
- **Pre-Commit**: Run `make format` before committing

### Testing Patterns
```python
# Pattern: arrange, act, assert
def test_create_note(test_client, test_db):
    response = test_client.post("/notes/", json={"title": "Test", "content": "..."})
    assert response.status_code == 201
    assert response.json()["title"] == "Test"
```

### API Design
- **Request/Response**: Use Pydantic schemas for validation
- **Status Codes**: 200 (OK), 201 (Created), 404 (Not Found), 400 (Bad Request)
- **Error Responses**: Return JSON with error details (use `HTTPException`)

## Common Development Workflows

### When Adding a New Endpoint
1. Define Pydantic schema in `backend/app/schemas.py`
2. Add SQLAlchemy model or extend existing in `backend/app/models.py`
3. Create router endpoint in appropriate file under `backend/app/routers/`
4. Add tests in corresponding `backend/tests/test_*.py`
5. Run `make test` to verify, then `make format` before committing

### When Fixing Code Style Issues
```bash
make format     # Auto-fix Black + Ruff issues
make lint       # Check remaining violations
```

### When Debugging Tests
- Use `make test` for quick feedback
- Tests use in-memory SQLite (temp file per test, cleaned up after)
- Check `conftest.py` for available fixture: `client` (creates isolated TestClient + temp SQLite DB)

## Key Files & Their Purpose

| File | Purpose |
|------|---------|
| [assignment.md](assignment.md) | Full week requirements, learning resources, automation examples |
| [docs/TASKS.md](docs/TASKS.md) | 7 workflow areas ready for automation (search, CRUD, extraction, validation, etc.) |
| [Makefile](Makefile) | Build commands (run, test, format, lint, seed) |
| [pre-commit-config.yaml](pre-commit-config.yaml) | Code quality enforcement hooks |
| [backend/app/main.py](backend/app/main.py) | FastAPI app init, startup events, CORS config |
| [backend/app/schemas.py](backend/app/schemas.py) | Pydantic request/response schemas |
| [backend/tests/conftest.py](backend/tests/conftest.py) | Pytest `client` fixture — isolated TestClient with temp SQLite DB |
| [backend/app/services/extract.py](backend/app/services/extract.py) | Action item text extraction (bullet lines ending in `!` or starting with `TODO:`) |
| [data/seed.sql](data/seed.sql) | SQLite schema + initial sample data |

## Automation Opportunities

Seven documented workflow areas in [docs/TASKS.md](docs/TASKS.md):
1. Pre-commit setup & formatting fixes
2. Add note search endpoint (case-insensitive)
3. Complete action-item flow
4. Enhance extraction logic (tags parsing)
5. Notes CRUD (edit, delete endpoints)
6. Add validation & error handling
7. API docs drift checking

Each area is ready for Claude Code custom commands, SubAgents, or MCP server integration.

## Related Resources

- **Assignment Details**: [assignment.md](assignment.md)
- **Development Tasks**: [docs/TASKS.md](docs/TASKS.md)
- **Build System**: [Makefile](Makefile)
- **Code Quality**: [pre-commit-config.yaml](pre-commit-config.yaml)
- **Seed Data**: [data/seed.sql](data/seed.sql)

## Agent Tips

✓ **Always set `PYTHONPATH=.`** before running Python/pytest commands  
✓ **Check TASKS.md first** when unsure what to work on next  
✓ **Run `make test`** to verify changes don't break tests  
✓ **Use `make format`** before committing to avoid pre-commit failures  
✓ **Frontend is static** — changes to HTML/CSS don't require a build step  
