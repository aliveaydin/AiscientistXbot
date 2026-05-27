from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
import os
import asyncio
import logging
from datetime import datetime
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.database import init_db
from app.routes import dashboard, tweets, articles, settings_route, blog, lab, public, rl_envs, rlforge, users, admin, marketing, agents, feedback, email as email_routes
from app.services.scheduler_service import scheduler_service
from app.services.article_service import ArticleService
from app.services.training_service import TrainingService
from app.database import async_session
from app.rate_limit import limiter

logger = logging.getLogger("app")


async def _seed_template_envs():
    """Load template environments into the database if not already present."""
    import glob as glob_mod
    from app.models import RLEnvironment
    from sqlalchemy import select

    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    if not os.path.isdir(templates_dir):
        return

    template_meta = {
        "gridworld_maze": {"name": "Gridworld Maze", "domain": "game", "difficulty": "easy", "category": "game",
                           "description": "10x10 grid maze navigation with random walls. Agent must find path to goal."},
        "stock_trading_5": {"name": "5-Stock Trading", "domain": "finance", "difficulty": "medium", "category": "finance",
                            "description": "5-stock portfolio trading with synthetic GBM prices, transaction costs, and Sharpe-based reward."},
        "cart_pole_wind": {"name": "CartPole with Wind", "domain": "control", "difficulty": "easy", "category": "control",
                           "description": "Classic CartPole with random wind disturbance. Keep pole balanced despite wind forces."},
        "inventory_mgmt": {"name": "Inventory Management", "domain": "optimization", "difficulty": "medium", "category": "optimization",
                           "description": "Warehouse inventory optimization for 3 products with stochastic demand."},
        "drone_grid_nav": {"name": "Drone Grid Navigation", "domain": "robotics", "difficulty": "hard", "category": "robotics",
                           "description": "3D drone obstacle avoidance. Navigate to goal while avoiding random obstacles."},
    }

    async with async_session() as db:
        for py_file in sorted(glob_mod.glob(os.path.join(templates_dir, "*.py"))):
            stem = os.path.basename(py_file).replace(".py", "")
            meta = template_meta.get(stem)
            if not meta:
                continue

            slug = stem.replace("_", "-")
            existing = await db.execute(select(RLEnvironment).where(RLEnvironment.slug == slug))
            if existing.scalar_one_or_none():
                continue

            with open(py_file, "r") as f:
                code = f.read()

            env = RLEnvironment(
                name=meta["name"], slug=slug, description=meta["description"],
                category=meta["category"], domain=meta["domain"], difficulty=meta["difficulty"],
                code=code, status="published", is_template=True,
                published_at=datetime.utcnow(),
            )
            db.add(env)
            logger.info("Seeded template env: %s", meta["name"])

        await db.commit()


async def _seed_subscription_plans():
    """Seed default subscription plans if not already present."""
    from app.models import SubscriptionPlan
    from sqlalchemy import select

    plans = [
        {
            "name": "free", "display_name": "Free", "price_monthly": 0,
            "monthly_credits": 0, "max_environments": 1, "max_training_steps": 50000,
            "pdf_download": False, "github_export": False, "can_buy_credits": False,
        },
        {
            "name": "starter", "display_name": "Starter", "price_monthly": 19,
            "monthly_credits": 0, "max_environments": 5, "max_training_steps": 500000,
            "pdf_download": True, "github_export": True, "can_buy_credits": True,
        },
        {
            "name": "pro", "display_name": "Pro", "price_monthly": 49,
            "monthly_credits": 0, "max_environments": 20, "max_training_steps": 2000000,
            "pdf_download": True, "github_export": True, "can_buy_credits": True,
        },
        {
            "name": "lab", "display_name": "Lab", "price_monthly": 149,
            "monthly_credits": 0, "max_environments": 100, "max_training_steps": 5000000,
            "pdf_download": True, "github_export": True, "can_buy_credits": True,
        },
    ]

    async with async_session() as db:
        for plan_data in plans:
            result = await db.execute(
                select(SubscriptionPlan).where(SubscriptionPlan.name == plan_data["name"])
            )
            existing = result.scalar_one_or_none()
            if existing:
                for key, val in plan_data.items():
                    if key != "name":
                        setattr(existing, key, val)
                logger.info("Updated subscription plan: %s", plan_data["display_name"])
            else:
                db.add(SubscriptionPlan(**plan_data))
                logger.info("Seeded subscription plan: %s", plan_data["display_name"])
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    await init_db()

    # Apply additive ALTER TABLE migrations for advanced research settings.
    try:
        from migrate_advanced_settings import migrate_from_url
        from app.config import settings as _settings
        migrate_from_url(_settings.database_url)
    except Exception as e:  # never block startup on a migration hiccup
        logger.warning("advanced_settings migration skipped: %s", e)

    async with async_session() as db:
        await ArticleService.scan_and_import_articles(db)

    await _seed_template_envs()
    await _seed_subscription_plans()

    training_svc = TrainingService()
    await training_svc.recover_orphan_runs()

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
    title="kualia.ai API",
    description="AI-powered RL environment generation, training, and research platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
app.include_router(rl_envs.router)
app.include_router(rlforge.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(marketing.router)
app.include_router(agents.router)
app.include_router(feedback.router)
app.include_router(email_routes.router)

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
