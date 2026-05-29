"""
Admin API endpoints for CRM-style platform management.
Lists users, environments, papers, and platform stats.
All endpoints require admin authentication.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, case
from typing import Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.auth import require_admin
from app.models import (
    User, RLEnvironment, TrainingRun, ResearchProject, ResearchPaper,
    SubscriptionPlan, CreditTransaction,
)

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/stats")
async def admin_stats(db: AsyncSession = Depends(get_db)):
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    total_envs = (await db.execute(
        select(func.count(RLEnvironment.id)).where(RLEnvironment.is_template == False)
    )).scalar() or 0
    total_training = (await db.execute(select(func.count(TrainingRun.id)))).scalar() or 0
    total_projects = (await db.execute(select(func.count(ResearchProject.id)))).scalar() or 0
    total_papers = (await db.execute(select(func.count(ResearchPaper.id)))).scalar() or 0

    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_7d = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= week_ago)
    )).scalar() or 0
    new_envs_7d = (await db.execute(
        select(func.count(RLEnvironment.id)).where(
            RLEnvironment.created_at >= week_ago,
            RLEnvironment.is_template == False,
        )
    )).scalar() or 0
    new_training_7d = (await db.execute(
        select(func.count(TrainingRun.id)).where(TrainingRun.created_at >= week_ago)
    )).scalar() or 0
    new_papers_7d = (await db.execute(
        select(func.count(ResearchPaper.id)).where(ResearchPaper.created_at >= week_ago)
    )).scalar() or 0

    completed_training = (await db.execute(
        select(func.count(TrainingRun.id)).where(TrainingRun.status == "completed")
    )).scalar() or 0
    failed_training = (await db.execute(
        select(func.count(TrainingRun.id)).where(TrainingRun.status == "failed")
    )).scalar() or 0

    # Credit stats
    total_credits_balance = (await db.execute(
        select(func.sum(User.credit_balance))
    )).scalar() or 0
    total_credits_consumed = (await db.execute(
        select(func.sum(func.abs(CreditTransaction.amount))).where(CreditTransaction.amount < 0)
    )).scalar() or 0
    credits_consumed_7d = (await db.execute(
        select(func.sum(func.abs(CreditTransaction.amount))).where(
            CreditTransaction.amount < 0,
            CreditTransaction.created_at >= week_ago,
        )
    )).scalar() or 0

    return {
        "total_users": total_users,
        "total_environments": total_envs,
        "total_training_runs": total_training,
        "total_projects": total_projects,
        "total_papers": total_papers,
        "completed_training": completed_training,
        "failed_training": failed_training,
        "total_credits_balance": round(total_credits_balance, 2),
        "total_credits_consumed": round(total_credits_consumed, 2),
        "last_7_days": {
            "new_users": new_users_7d,
            "new_environments": new_envs_7d,
            "new_training_runs": new_training_7d,
            "new_papers": new_papers_7d,
            "credits_consumed": round(credits_consumed_7d, 2),
        },
    }


@router.get("/users")
async def admin_users(
    search: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(User).order_by(desc(User.created_at))
    if search:
        query = query.where(
            User.username.ilike(f"%{search}%") | User.email.ilike(f"%{search}%") | User.display_name.ilike(f"%{search}%")
        )
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    rows = (await db.execute(query.offset(offset).limit(limit))).scalars().all()

    users = []
    for u in rows:
        env_count = (await db.execute(
            select(func.count(RLEnvironment.id)).where(RLEnvironment.user_id == u.id)
        )).scalar() or 0
        training_count = (await db.execute(
            select(func.count(TrainingRun.id)).where(
                TrainingRun.env_id.in_(select(RLEnvironment.id).where(RLEnvironment.user_id == u.id))
            )
        )).scalar() or 0
        research_count = (await db.execute(
            select(func.count(ResearchProject.id)).where(ResearchProject.user_id == u.id)
        )).scalar() or 0

        plan_name = None
        if u.plan_id:
            plan = (await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == u.plan_id))).scalar_one_or_none()
            plan_name = plan.display_name if plan else None

        users.append({
            "id": u.id,
            "clerk_id": u.clerk_id,
            "username": u.username,
            "email": u.email,
            "display_name": u.display_name,
            "avatar_url": u.avatar_url,
            "bio": u.bio,
            "credit_balance": round(u.credit_balance or 0, 4),
            "plan": plan_name,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "env_count": env_count,
            "training_count": training_count,
            "research_count": research_count,
        })

    return {"total": total, "users": users}


@router.get("/users/{user_id}")
async def admin_user_detail(user_id: int, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        return {"error": "User not found"}

    envs = (await db.execute(
        select(RLEnvironment).where(RLEnvironment.user_id == user_id).order_by(desc(RLEnvironment.created_at))
    )).scalars().all()

    projects = (await db.execute(
        select(ResearchProject).where(ResearchProject.user_id == user_id).order_by(desc(ResearchProject.created_at))
    )).scalars().all()

    env_ids = [e.id for e in envs]
    training_runs = []
    if env_ids:
        training_runs = (await db.execute(
            select(TrainingRun).where(TrainingRun.env_id.in_(env_ids)).order_by(desc(TrainingRun.created_at))
        )).scalars().all()

    plan_name = None
    if user.plan_id:
        plan = (await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == user.plan_id))).scalar_one_or_none()
        plan_name = plan.display_name if plan else None

    recent_tx = (await db.execute(
        select(CreditTransaction).where(CreditTransaction.user_id == user_id)
        .order_by(CreditTransaction.created_at.desc()).limit(20)
    )).scalars().all()

    return {
        "user": {
            "id": user.id,
            "clerk_id": user.clerk_id,
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "bio": user.bio,
            "credit_balance": round(user.credit_balance or 0, 4),
            "plan": plan_name,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "credit_transactions": [{
            "id": t.id, "amount": t.amount, "balance_after": t.balance_after,
            "operation": t.operation, "created_at": t.created_at.isoformat() if t.created_at else None,
        } for t in recent_tx],
        "environments": [{
            "id": e.id, "name": e.name, "category": e.category, "status": e.status,
            "version": e.version, "created_at": e.created_at.isoformat() if e.created_at else None,
        } for e in envs],
        "training_runs": [{
            "id": t.id, "env_id": t.env_id, "algorithm": t.algorithm, "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        } for t in training_runs],
        "research_projects": [{
            "id": p.id, "title": p.title, "status": p.status, "current_phase": p.current_phase,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        } for p in projects],
    }


@router.get("/environments")
async def admin_environments(
    search: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(RLEnvironment).where(RLEnvironment.is_template == False).order_by(desc(RLEnvironment.created_at))
    if search:
        query = query.where(RLEnvironment.name.ilike(f"%{search}%"))
    if category:
        query = query.where(RLEnvironment.category == category)
    if status:
        query = query.where(RLEnvironment.status == status)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    rows = (await db.execute(query.offset(offset).limit(limit))).scalars().all()

    envs = []
    for e in rows:
        owner_name = None
        if e.user_id:
            owner = (await db.execute(select(User.username, User.email).where(User.id == e.user_id))).first()
            if owner:
                owner_name = owner.username or owner.email

        training_count = (await db.execute(
            select(func.count(TrainingRun.id)).where(TrainingRun.env_id == e.id)
        )).scalar() or 0

        envs.append({
            "id": e.id, "name": e.name, "slug": e.slug, "category": e.category,
            "domain": e.domain, "difficulty": e.difficulty, "status": e.status,
            "version": e.version, "ai_model_used": e.ai_model_used,
            "user_id": e.user_id, "owner": owner_name,
            "training_count": training_count,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        })

    return {"total": total, "environments": envs}


@router.get("/papers")
async def admin_papers(
    search: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(ResearchPaper).order_by(desc(ResearchPaper.created_at))
    if search:
        query = query.where(ResearchPaper.title.ilike(f"%{search}%"))
    if status:
        query = query.where(ResearchPaper.status == status)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    rows = (await db.execute(query.offset(offset).limit(limit))).scalars().all()

    papers = []
    for p in rows:
        project = (await db.execute(
            select(ResearchProject.title, ResearchProject.user_id).where(ResearchProject.id == p.project_id)
        )).first()
        project_title = project.title if project else None
        owner_name = None
        if project and project.user_id:
            owner = (await db.execute(select(User.username, User.email).where(User.id == project.user_id))).first()
            if owner:
                owner_name = owner.username or owner.email

        papers.append({
            "id": p.id, "title": p.title, "abstract": (p.abstract or "")[:200],
            "status": p.status, "version": p.version,
            "published": p.published,
            "project_id": p.project_id, "project_title": project_title,
            "owner": owner_name,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "published_at": p.published_at.isoformat() if p.published_at else None,
        })

    return {"total": total, "papers": papers}


@router.post("/users/{user_id}/add-credits")
async def admin_add_credits(user_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    """Admin: manually add credits to a user."""
    from app.services.credit_service import credit_service
    amount = data.get("amount", 0)
    reason = data.get("reason", "admin_grant")
    if amount <= 0:
        return {"error": "Amount must be positive"}
    result = await credit_service.add_credits(
        user_id, amount, "admin_grant", db,
        details={"reason": reason},
    )
    return result


@router.post("/users/{user_id}/set-plan")
async def admin_set_plan(user_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    """Admin: change a user's subscription plan."""
    plan_name = data.get("plan")
    plan = (await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.name == plan_name)
    )).scalar_one_or_none()
    if not plan:
        return {"error": f"Plan '{plan_name}' not found"}
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        return {"error": "User not found"}
    user.plan_id = plan.id
    user.plan_started_at = datetime.utcnow()
    await db.commit()
    return {"ok": True, "plan": plan.display_name, "user_id": user_id}
