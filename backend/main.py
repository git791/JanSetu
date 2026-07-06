"""
JanSetu AI Constituency Intelligence Platform — FastAPI Application Entry Point
"""

import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

load_dotenv()

from routes.submissions import router as submissions_router
from routes.clusters import router as clusters_router
from routes.simulate import router as simulate_router
from utils.bigquery_client import init_bigquery
from utils.firestore_client import init_firestore


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle handler."""
    # ── Startup ───────────────────────────────────────────────────────────────
    print("🚀  JanSetu API starting …")
    init_bigquery()
    init_firestore()
    print("✅  Clients initialised (BigQuery + Firestore)")
    yield
    # ── Shutdown ──────────────────────────────────────────────────────────────
    print("🛑  JanSetu API shutting down …")


app = FastAPI(
    title="JanSetu API",
    description="AI-powered Constituency Intelligence Platform for Varanasi Cantonment",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
_frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
_allowed_origins = list(
    {_frontend_url, "http://localhost:5173", "http://localhost:3000"}
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(submissions_router)
app.include_router(clusters_router)
app.include_router(simulate_router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "service": "JanSetu API"}

# ── Static Files (React Frontend) ─────────────────────────────────────────────
# In production (Cloud Run), the frontend is built into the 'static' directory.
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    # Mount the Vite assets folder directly
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_react_app(full_path: str):
        # Allow serving static files directly (like vite.svg, etc)
        file_path = os.path.join(static_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        # Fallback to index.html for React Router
        return FileResponse(os.path.join(static_dir, "index.html"))


# ── Dev runner ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
