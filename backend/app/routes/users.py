"""
User-facing API endpoints for authenticated users.
Handles user sync, profile, and user-scoped resource listing.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.auth import get_current_user, get_optional_user
from app.models import User, RLEnvironment, TrainingRun, ResearchProject, SubscriptionPlan, CreditTransaction

router = APIRouter(prefix="/api/users", tags=["users"])


class UserSyncRequest(BaseModel):
    username: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None


class UserUpdateRequest(BaseModel):
    username: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None


# ─── Helpers ───

async def _get_or_create_user(db: AsyncSession, clerk_user_id: str, email: Optional[str] = None) -> User:
    result = await db.execute(select(User).where(User.clerk_id == clerk_user_id))
    user = result.scalar_one_or_none()
    if user:
        # Auto-assign Free plan to existing users who don't have one
        if not user.plan_id:
            free_plan = (await db.execute(
                select(SubscriptionPlan).where(SubscriptionPlan.name == "free")
            )).scalar_one_or_none()
            if free_plan:
                WELCOME_CREDIT = 5.0
                user.plan_id = free_plan.id
                if (user.credit_balance or 0) == 0:
                    user.credit_balance = WELCOME_CREDIT
                    tx = CreditTransaction(
                        user_id=user.id,
                        amount=WELCOME_CREDIT,
                        balance_after=user.credit_balance,
                        operation="welcome_credit",
                        details_json='{"plan": "free", "reason": "plan_migration"}',
                    )
                    db.add(tx)
                user.plan_started_at = datetime.utcnow()
                await db.commit()
                await db.refresh(user)
        return user

    # Auto-generate a username from clerk_id
    base_username = f"user_{clerk_user_id[-8:]}"

    # Find the Free plan
    free_plan = (await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.name == "free")
    )).scalar_one_or_none()

    WELCOME_CREDIT = 5.0
    user = User(
        clerk_id=clerk_user_id,
        email=email,
        username=base_username,
        display_name=base_username,
        plan_id=free_plan.id if free_plan else None,
        credit_balance=WELCOME_CREDIT if free_plan else 0,
        plan_started_at=datetime.utcnow(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    if free_plan:
        tx = CreditTransaction(
            user_id=user.id,
            amount=WELCOME_CREDIT,
            balance_after=user.credit_balance,
            operation="welcome_credit",
            details_json='{"plan": "free", "reason": "new_user_signup"}',
        )
        db.add(tx)
        await db.commit()

    # Send welcome email (fire-and-forget)
    if email:
        try:
            from app.services.email_service import email_service
            await email_service.send_transactional(
                to=email, template="welcome", data={}, user_id=user.id,
            )
        except Exception:
            pass

    return user


async def _serialize_user(user: User, db: AsyncSession) -> dict:
    plan_info = None
    if user.plan_id:
        plan = (await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == user.plan_id)
        )).scalar_one_or_none()
        if plan:
            plan_info = {
                "name": plan.name,
                "display_name": plan.display_name,
                "price_monthly": plan.price_monthly,
                "monthly_credits": plan.monthly_credits,
                "max_environments": plan.max_environments,
                "max_training_steps": plan.max_training_steps,
                "pdf_download": plan.pdf_download,
                "github_export": plan.github_export,
            }
    return {
        "id": user.id,
        "clerk_id": user.clerk_id,
        "email": user.email,
        "username": user.username,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "credit_balance": round(user.credit_balance or 0, 4),
        "plan": plan_info,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


# ─── Endpoints ───

@router.post("/sync")
async def sync_user(
    body: UserSyncRequest,
    auth: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Called on first login / periodically to sync Clerk user data to our DB.
    Creates the user if not exists, updates fields if changed.
    """
    clerk_id = auth["clerk_user_id"]
    user = await _get_or_create_user(db, clerk_id, auth.get("email"))

    changed = False
    if body.email and body.email != user.email:
        user.email = body.email
        changed = True
    if body.display_name and body.display_name != user.display_name:
        user.display_name = body.display_name
        changed = True
    if body.avatar_url and body.avatar_url != user.avatar_url:
        user.avatar_url = body.avatar_url
        changed = True
    if body.username and body.username != user.username:
        existing = await db.execute(select(User).where(User.username == body.username, User.id != user.id))
        if not existing.scalar_one_or_none():
            user.username = body.username
            changed = True

    if changed:
        user.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)

    return await _serialize_user(user, db)


@router.get("/me")
async def get_me(
    auth: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current authenticated user's profile."""
    user = await _get_or_create_user(db, auth["clerk_user_id"], auth.get("email"))
    return await _serialize_user(user, db)


@router.patch("/me")
async def update_me(
    body: UserUpdateRequest,
    auth: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's profile."""
    user = await _get_or_create_user(db, auth["clerk_user_id"], auth.get("email"))

    if body.username is not None:
        if body.username != user.username:
            existing = await db.execute(select(User).where(User.username == body.username, User.id != user.id))
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=409, detail="Username already taken")
            user.username = body.username

    if body.display_name is not None:
        user.display_name = body.display_name
    if body.bio is not None:
        user.bio = body.bio

    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    return await _serialize_user(user, db)


@router.get("/me/environments")
async def get_my_environments(
    auth: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """Get all environments owned by the current user."""
    user = await _get_or_create_user(db, auth["clerk_user_id"])

    count_q = select(func.count()).select_from(RLEnvironment).where(RLEnvironment.user_id == user.id)
    total = (await db.execute(count_q)).scalar() or 0

    q = (
        select(RLEnvironment)
        .where(RLEnvironment.user_id == user.id)
        .order_by(desc(RLEnvironment.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(q)
    envs = result.scalars().all()

    import json as _json

    env_ids = [e.id for e in envs]
    training_map: dict = {}
    if env_ids:
        latest_runs_q = (
            select(TrainingRun)
            .where(TrainingRun.env_id.in_(env_ids), TrainingRun.status == "completed")
            .order_by(desc(TrainingRun.id))
        )
        all_completed = (await db.execute(latest_runs_q)).scalars().all()
        for r in all_completed:
            if r.env_id not in training_map:
                res = _json.loads(r.results_json) if r.results_json else {}
                training_map[r.env_id] = {
                    "algorithm": r.algorithm,
                    "mean_reward": res.get("mean_reward"),
                    "success_rate": res.get("success_rate"),
                    "total_timesteps": res.get("total_timesteps"),
                    "training_time_sec": res.get("training_time_sec"),
                }

    return {
        "total": total,
        "items": [
            {
                "id": e.id,
                "name": e.name,
                "slug": e.slug,
                "description": e.description,
                "category": e.category,
                "domain": e.domain,
                "difficulty": e.difficulty,
                "status": e.status,
                "version": e.version,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "updated_at": e.updated_at.isoformat() if e.updated_at else None,
                "training": training_map.get(e.id),
            }
            for e in envs
        ],
    }


@router.get("/me/training")
async def get_my_training(
    auth: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """Get training runs for the current user's environments."""
    user = await _get_or_create_user(db, auth["clerk_user_id"])

    user_env_ids = select(RLEnvironment.id).where(RLEnvironment.user_id == user.id)

    count_q = select(func.count()).select_from(TrainingRun).where(TrainingRun.env_id.in_(user_env_ids))
    total = (await db.execute(count_q)).scalar() or 0

    q = (
        select(TrainingRun, RLEnvironment.name.label("env_name"))
        .join(RLEnvironment, TrainingRun.env_id == RLEnvironment.id)
        .where(RLEnvironment.user_id == user.id)
        .order_by(desc(TrainingRun.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(q)
    rows = result.all()

    import json

    return {
        "total": total,
        "items": [
            {
                "id": run.id,
                "env_id": run.env_id,
                "env_name": env_name,
                "algorithm": run.algorithm,
                "status": run.status,
                "config": json.loads(run.config_json) if run.config_json else None,
                "results": json.loads(run.results_json) if run.results_json else None,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "created_at": run.created_at.isoformat() if run.created_at else None,
            }
            for run, env_name in rows
        ],
    }


@router.get("/me/research")
async def get_my_research(
    auth: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """Get research projects owned by the current user."""
    user = await _get_or_create_user(db, auth["clerk_user_id"])

    count_q = select(func.count()).select_from(ResearchProject).where(ResearchProject.user_id == user.id)
    total = (await db.execute(count_q)).scalar() or 0

    q = (
        select(ResearchProject)
        .where(ResearchProject.user_id == user.id)
        .order_by(desc(ResearchProject.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(q)
    projects = result.scalars().all()

    return {
        "total": total,
        "items": [
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "status": p.status,
                "current_phase": p.current_phase,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in projects
        ],
    }


@router.get("/plans")
async def list_plans(db: AsyncSession = Depends(get_db)):
    """List all available subscription plans (public)."""
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.is_active == True).order_by(SubscriptionPlan.price_monthly)
    )
    plans = result.scalars().all()
    return [
        {
            "id": p.id, "name": p.name, "display_name": p.display_name,
            "price_monthly": p.price_monthly, "monthly_credits": p.monthly_credits,
            "max_environments": p.max_environments, "max_training_steps": p.max_training_steps,
            "pdf_download": p.pdf_download, "github_export": p.github_export,
            "can_buy_credits": p.can_buy_credits,
        }
        for p in plans
    ]


@router.get("/{username}")
async def get_public_profile(
    username: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a user's public profile by username."""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Public environments
    env_q = (
        select(RLEnvironment)
        .where(RLEnvironment.user_id == user.id, RLEnvironment.status == "published")
        .order_by(desc(RLEnvironment.created_at))
        .limit(20)
    )
    envs = (await db.execute(env_q)).scalars().all()

    # Public research papers count
    research_q = select(func.count()).select_from(ResearchProject).where(
        ResearchProject.user_id == user.id, ResearchProject.status == "completed"
    )
    research_count = (await db.execute(research_q)).scalar() or 0

    return {
        "user": {
            "username": user.username,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "bio": user.bio,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "environments": [
            {
                "id": e.id,
                "name": e.name,
                "slug": e.slug,
                "description": e.description,
                "category": e.category,
                "difficulty": e.difficulty,
            }
            for e in envs
        ],
        "research_count": research_count,
    }


# ─── Credit & Subscription Endpoints ───

@router.get("/me/credits")
async def get_credits(auth: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.services.credit_service import credit_service
    user = await _get_or_create_user(db, auth["clerk_user_id"], auth.get("email"))
    balance = await credit_service.get_balance(user.id, db)
    plan = await credit_service.get_plan(user.id, db)
    monthly = await credit_service.get_monthly_usage(user.id, db)
    return {
        "balance": round(balance, 4),
        "plan": plan,
        "monthly_usage": monthly,
    }


@router.get("/me/credit-history")
async def get_credit_history(
    limit: int = 50,
    offset: int = 0,
    auth: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.credit_service import credit_service
    user = await _get_or_create_user(db, auth["clerk_user_id"], auth.get("email"))
    return await credit_service.get_usage_history(user.id, db, limit=limit, offset=offset)


@router.get("/me/subscription")
async def get_subscription(
    auth: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Full subscription overview: plan, usage, limits, history."""
    from app.services.credit_service import credit_service, ADMIN_EMAILS

    user = await _get_or_create_user(db, auth["clerk_user_id"], auth.get("email"))
    is_admin = bool(user.email and user.email.lower() in [e.lower() for e in ADMIN_EMAILS])

    plan = await credit_service.get_plan(user.id, db)
    monthly = await credit_service.get_monthly_usage(user.id, db)

    env_count = (await db.execute(
        select(func.count(RLEnvironment.id)).where(RLEnvironment.user_id == user.id)
    )).scalar() or 0

    research_count = (await db.execute(
        select(func.count(ResearchProject.id)).where(ResearchProject.user_id == user.id)
    )).scalar() or 0

    from app.models import TrainingRun
    training_count = (await db.execute(
        select(func.count(TrainingRun.id))
        .join(RLEnvironment, TrainingRun.env_id == RLEnvironment.id)
        .where(RLEnvironment.user_id == user.id)
    )).scalar() or 0

    all_plans = (await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.is_active == True).order_by(SubscriptionPlan.price_monthly)
    )).scalars().all()

    recent_tx = (await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.user_id == user.id)
        .order_by(CreditTransaction.created_at.desc())
        .limit(20)
    )).scalars().all()

    return {
        "is_admin": is_admin,
        "balance": round(user.credit_balance or 0, 4),
        "plan": plan,
        "plan_started_at": user.plan_started_at.isoformat() if user.plan_started_at else None,
        "plan_period_end": user.plan_period_end.isoformat() if user.plan_period_end else None,
        "usage": {
            "environments": env_count,
            "training_runs": training_count,
            "research_projects": research_count,
            "monthly": monthly,
        },
        "limits": {
            "max_environments": plan["max_environments"] if plan else 3,
            "max_training_steps": plan["max_training_steps"] if plan else 50000,
            "pdf_download": plan["pdf_download"] if plan else False,
            "github_export": plan["github_export"] if plan else False,
            "can_buy_credits": plan["can_buy_credits"] if plan else False,
        },
        "available_plans": [
            {
                "id": p.id, "name": p.name, "display_name": p.display_name,
                "price_monthly": p.price_monthly, "monthly_credits": p.monthly_credits,
                "max_environments": p.max_environments, "max_training_steps": p.max_training_steps,
                "pdf_download": p.pdf_download, "github_export": p.github_export,
                "can_buy_credits": p.can_buy_credits,
            }
            for p in all_plans
        ],
        "recent_transactions": [{
            "id": t.id,
            "amount": t.amount,
            "balance_after": t.balance_after,
            "operation": t.operation,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        } for t in recent_tx],
    }
