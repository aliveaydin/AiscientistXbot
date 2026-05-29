"""
Feedback API — user submission + admin management + AI analysis.
"""
import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_user, require_admin
from app.models import Feedback, User
from app.services.ai_service import ai_service

logger = logging.getLogger("feedback")

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

ANALYZE_SYSTEM_PROMPT = """You are a product feedback analyst for kualia.ai — an AI platform for RL environment generation, agent training, and research paper writing.

Analyze the user feedback below and return a JSON object with these fields:
- category: one of ["ui_bug", "backend_bug", "feature_request", "ux_improvement", "performance", "documentation", "pricing", "praise", "question", "other"]
- priority: one of ["critical", "high", "medium", "low"]
- sentiment: one of ["positive", "neutral", "negative", "frustrated"]
- summary: A concise 1-sentence summary of what the user is reporting or requesting.
- suggested_action: A concrete next step for the development team (e.g. "Fix the 500 error on /builder/[id] when training completes", "Add dark mode toggle to settings page").
- is_duplicate_hint: A short phrase describing what to search for to check if this is a duplicate (e.g. "training timeout error", "mobile layout broken").

Rules:
- Be objective and precise.
- Priority should reflect user impact: critical = platform broken/data loss, high = feature unusable, medium = annoying but workaround exists, low = nice-to-have.
- Return ONLY valid JSON. No explanation."""


class FeedbackSubmit(BaseModel):
    type: str = "general"
    title: str
    body: str
    page_url: Optional[str] = None


class FeedbackUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    admin_notes: Optional[str] = None


# ─── User endpoints ───

@router.post("/submit")
async def submit_feedback(
    req: FeedbackSubmit,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(
        select(User).where(User.clerk_id == current_user["clerk_user_id"])
    )).scalar_one_or_none()

    fb = Feedback(
        user_id=user.id if user else None,
        user_email=user.email if user else current_user.get("email"),
        user_name=user.display_name or user.username if user else None,
        type=req.type,
        title=req.title,
        body=req.body,
        page_url=req.page_url,
    )
    db.add(fb)
    await db.commit()
    await db.refresh(fb)

    # Fire-and-forget AI analysis
    try:
        user_prompt = f"Type: {req.type}\nTitle: {req.title}\nBody: {req.body}\nPage: {req.page_url or 'N/A'}"
        raw = await ai_service._call_ai(ANALYZE_SYSTEM_PROMPT, user_prompt, max_tokens=500)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        analysis = json.loads(raw)
        fb.ai_category = analysis.get("category")
        fb.priority = analysis.get("priority")
        fb.ai_sentiment = analysis.get("sentiment")
        fb.ai_summary = analysis.get("summary")
        fb.ai_suggested_action = analysis.get("suggested_action")
        await db.commit()
        logger.info("Feedback #%d analyzed: %s / %s", fb.id, fb.ai_category, fb.priority)
    except Exception as e:
        logger.warning("AI analysis failed for feedback #%d: %s", fb.id, e)

    return {"id": fb.id, "status": "submitted", "message": "Thank you for your feedback!"}


@router.get("/mine")
async def my_feedback(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(
        select(User).where(User.clerk_id == current_user["clerk_user_id"])
    )).scalar_one_or_none()
    if not user:
        return {"items": []}

    result = await db.execute(
        select(Feedback)
        .where(Feedback.user_id == user.id)
        .order_by(desc(Feedback.created_at))
        .limit(50)
    )
    items = result.scalars().all()
    return {"items": [_serialize(f) for f in items]}


# ─── Admin endpoints ───

@router.get("/all")
async def list_all_feedback(
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    q = select(Feedback)
    if status:
        q = q.where(Feedback.status == status)
    if type:
        q = q.where(Feedback.type == type)
    if priority:
        q = q.where(Feedback.priority == priority)
    q = q.order_by(desc(Feedback.created_at)).offset(offset).limit(limit)

    items = (await db.execute(q)).scalars().all()

    count_q = select(func.count(Feedback.id))
    if status:
        count_q = count_q.where(Feedback.status == status)
    if type:
        count_q = count_q.where(Feedback.type == type)
    if priority:
        count_q = count_q.where(Feedback.priority == priority)
    total = (await db.execute(count_q)).scalar() or 0

    # Stats
    stats_result = await db.execute(
        select(
            func.count(Feedback.id).label("total"),
            func.count(Feedback.id).filter(Feedback.status == "new").label("new"),
            func.count(Feedback.id).filter(Feedback.status == "reviewed").label("reviewed"),
            func.count(Feedback.id).filter(Feedback.status == "in_progress").label("in_progress"),
            func.count(Feedback.id).filter(Feedback.status == "resolved").label("resolved"),
        )
    )
    stats_row = stats_result.one()

    return {
        "items": [_serialize(f, admin=True) for f in items],
        "total": total,
        "stats": {
            "total": stats_row.total,
            "new": stats_row.new,
            "reviewed": stats_row.reviewed,
            "in_progress": stats_row.in_progress,
            "resolved": stats_row.resolved,
        },
    }


@router.put("/{feedback_id}")
async def update_feedback(
    feedback_id: int,
    req: FeedbackUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    fb = (await db.execute(select(Feedback).where(Feedback.id == feedback_id))).scalar_one_or_none()
    if not fb:
        raise HTTPException(404, "Feedback not found")
    if req.status:
        fb.status = req.status
    if req.priority:
        fb.priority = req.priority
    if req.admin_notes is not None:
        fb.admin_notes = req.admin_notes
    await db.commit()
    return {"updated": True}


@router.post("/{feedback_id}/reanalyze")
async def reanalyze_feedback(
    feedback_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    fb = (await db.execute(select(Feedback).where(Feedback.id == feedback_id))).scalar_one_or_none()
    if not fb:
        raise HTTPException(404, "Feedback not found")

    user_prompt = f"Type: {fb.type}\nTitle: {fb.title}\nBody: {fb.body}\nPage: {fb.page_url or 'N/A'}"
    raw = await ai_service._call_ai(ANALYZE_SYSTEM_PROMPT, user_prompt, max_tokens=500)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    analysis = json.loads(raw)
    fb.ai_category = analysis.get("category")
    fb.priority = analysis.get("priority")
    fb.ai_sentiment = analysis.get("sentiment")
    fb.ai_summary = analysis.get("summary")
    fb.ai_suggested_action = analysis.get("suggested_action")
    fb.status = "reviewed"
    await db.commit()
    return {"updated": True, "analysis": analysis}


def _serialize(fb: Feedback, admin: bool = False) -> dict:
    d = {
        "id": fb.id,
        "type": fb.type,
        "title": fb.title,
        "body": fb.body,
        "status": fb.status,
        "priority": fb.priority,
        "ai_category": fb.ai_category,
        "ai_summary": fb.ai_summary,
        "ai_sentiment": fb.ai_sentiment,
        "created_at": fb.created_at.isoformat() if fb.created_at else None,
    }
    if admin:
        d.update({
            "user_email": fb.user_email,
            "user_name": fb.user_name,
            "page_url": fb.page_url,
            "ai_suggested_action": fb.ai_suggested_action,
            "admin_notes": fb.admin_notes,
            "updated_at": fb.updated_at.isoformat() if fb.updated_at else None,
        })
    return d
