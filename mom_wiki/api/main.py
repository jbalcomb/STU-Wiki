"""FastAPI application for Master of Magic Wiki Corpus."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .routes import router

# Frontend directory
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend" / "src"

app = FastAPI(
    title="Master of Magic Wiki Corpus API",
    description="REST API for accessing the MoM Wiki corpus data",
    version="0.1.0"
)

# CORS middleware for frontend access.
# Browsers reject `Access-Control-Allow-Origin: *` when credentials are
# allowed, so the wildcard here forces allow_credentials=False. If you need
# credentialed cross-origin requests, replace allow_origins with an explicit
# list of origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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


# Serve frontend static files
if FRONTEND_DIR.exists():
    @app.get("/app")
    @app.get("/app/")
    async def serve_index():
        """Serve the main graph explorer."""
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/admin")
    @app.get("/admin/")
    async def serve_admin():
        """Serve the admin panel."""
        return FileResponse(FRONTEND_DIR / "admin.html")

    # Mount static files for CSS/JS
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
