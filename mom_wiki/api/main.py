"""FastAPI application for Master of Magic Wiki Corpus."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from .routes import router

# Frontend directory
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend" / "src"

app = FastAPI(
    title="Master of Magic Wiki Corpus API",
    description="REST API for accessing the MoM Wiki corpus data",
    version="0.1.0"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Local dev, tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(router)


@app.get("/")
async def root():
    """API root - health check and info."""
    return {
        "name": "Master of Magic Wiki Corpus API",
        "version": "0.1.0",
        "status": "ok"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Serve the frontend.
#
# Mounting at /app with html=True means /app/ serves index.html and the
# browser can resolve relative ./styles.css, ./api.js, ./admin.html paths
# against /app/. The same files (with the same relative paths) also work
# under GitHub Pages serving the docs/ directory directly.
if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

    @app.get("/admin", include_in_schema=False)
    @app.get("/admin/", include_in_schema=False)
    async def admin_redirect():
        """Backward-compat redirect from the old /admin URL."""
        return RedirectResponse("/app/admin.html")
