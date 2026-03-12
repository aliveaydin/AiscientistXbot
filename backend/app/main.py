from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
import asyncio
import logging

from app.database import init_db
from app.routes import dashboard, tweets, articles, settings_route, blog, lab, public
from app.services.scheduler_service import scheduler_service
from app.services.article_service import ArticleService
from app.database import async_session

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    await init_db()

    async with async_session() as db:
        await ArticleService.scan_and_import_articles(db)

    logger.info("Twitter Bot AI Agent started!")
    logger.info("Dashboard: http://localhost:8000")
    logger.info("API Docs: http://localhost:8000/docs")

    # Auto-start the scheduler so it works after every container restart
    scheduler_service.start()
    logger.info("Scheduler auto-started on boot")

    # Run initial jobs in background after a short delay
    async def _delayed_initial():
        await asyncio.sleep(10)
        await scheduler_service.run_initial_jobs()

    asyncio.create_task(_delayed_initial())

    yield

    scheduler_service.stop()
    logger.info("Twitter Bot AI Agent stopped!")


app = FastAPI(
    title="Twitter Bot AI Agent",
    description="AI-powered Twitter bot that generates popular science tweets from articles",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check - must be before catch-all route
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "Twitter Bot AI Agent"}

# API Routes
app.include_router(dashboard.router)
app.include_router(tweets.router)
app.include_router(articles.router)
app.include_router(settings_route.router)
app.include_router(blog.router)
app.include_router(lab.router)
app.include_router(public.router)

# Serve frontend static files - check multiple possible locations
frontend_candidates = [
    os.getenv("FRONTEND_DIST_DIR", ""),
    os.path.join(os.path.dirname(__file__), "..", "frontend_dist"),  # Docker
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist"),  # Local dev
]

frontend_dir = None
for candidate in frontend_candidates:
    if candidate and os.path.exists(candidate):
        frontend_dir = os.path.abspath(candidate)
        break

if frontend_dir and os.path.exists(frontend_dir):
    assets_dir = os.path.join(frontend_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend for all non-API routes."""
        file_path = os.path.join(frontend_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dir, "index.html"))
