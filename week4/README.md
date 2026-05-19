# Developer's Command Center

A minimal full-stack application for managing notes and action items, designed as a playground for experimenting with Claude Code automations.

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy ORM + SQLite
- **Frontend**: Static HTML/CSS/JavaScript (no build step)
- **Testing**: pytest with isolated in-memory test DB
- **Code Quality**: Black + Ruff (enforced via pre-commit)

## Quick Start

### 1. Activate Python Environment

```bash
conda activate cs146s
```

### 2. Run the Application

```bash
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Access the App

- Frontend: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Development Commands

| Command | Description |
|---------|-------------|
| `make test` | Run pytest |
| `make format` | Format code with black + ruff |
| `make lint` | Check code quality |
| `make seed` | Seed database with sample data |

## Project Structure

```
backend/
  app/
    main.py          # FastAPI application
    models.py        # SQLAlchemy ORM models
    schemas.py       # Pydantic schemas
    db.py            # Database session management
    routers/         # API endpoints
    services/        # Business logic
  tests/             # Test suite

frontend/            # Static UI (HTML/CSS/JS)
data/                # SQLite database
docs/                # Task documentation
```

## License

MIT
