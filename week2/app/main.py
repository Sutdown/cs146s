"""
Main application entry point with proper lifecycle management.
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .db import init_db
from .routers import action_items, notes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# Application Lifecycle
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Action Item Extractor application...")
    init_db()
    logger.info("Application started successfully")

    yield  # Application runs here

    # Shutdown
    logger.info("Shutting down application...")


# ============================================================================
# Application Setup
# ============================================================================

app = FastAPI(
    title="Action Item Extractor",
    description="Extract actionable items from free-form notes using rule-based or LLM-powered extraction.",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================================
# Global Exception Handler
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred",
            "type": type(exc).__name__,
        },
    )


# ============================================================================
# Routes
# ============================================================================

@app.get(
    "/",
    response_class=HTMLResponse,
    summary="Home page",
    description="Serves the web interface."
)
def index() -> str:
    """
    Serve the main HTML page.
    """
    html_path = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    return html_path.read_text(encoding="utf-8")


@app.get(
    "/health",
    summary="Health check",
    description="Check if the application is running."
)
def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}


# Include routers
app.include_router(notes.router)
app.include_router(action_items.router)


# Mount static files
static_dir = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
