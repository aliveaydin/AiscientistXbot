"""
Email management routes — admin sends, logs, stats, and user preferences.
"""
import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.database import get_db
from app.auth import get_current_user, require_admin
from app.models import EmailLog, User
from app.services.email_service import email_service, _wrap_html

logger = logging.getLogger("email_api")

router = APIRouter(prefix="/api/email", tags=["email"])


# ─── Schemas ───

class SendEmailRequest(BaseModel):
    template: Optional[str] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    target: str = "all"  # all, free, starter, pro, lab, active, inactive
    channel: str = "marketing"


class EmailPrefsUpdate(BaseModel):
    email_notifications: Optional[bool] = None
    marketing_emails: Optional[bool] = None


# ─── Admin: Send emails ───

@router.post("/send")
async def admin_send_email(
    req: SendEmailRequest,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    """Send a marketing/transactional email to a user group."""
    from app.models import SubscriptionPlan

    query = select(User).where(User.email.isnot(None))

    if req.target == "free":
        sub = select(SubscriptionPlan.id).where(SubscriptionPlan.name == "free")
        query = query.where(User.plan_id.in_(sub))
    elif req.target == "starter":
        sub = select(SubscriptionPlan.id).where(SubscriptionPlan.name == "starter")
        query = query.where(User.plan_id.in_(sub))
    elif req.target == "pro":
        sub = select(SubscriptionPlan.id).where(SubscriptionPlan.name == "pro")
        query = query.where(User.plan_id.in_(sub))
    elif req.target == "lab":
        sub = select(SubscriptionPlan.id).where(SubscriptionPlan.name == "lab")
        query = query.where(User.plan_id.in_(sub))
    elif req.target == "active":
        cutoff = datetime.utcnow() - timedelta(days=7)
        query = query.where(User.updated_at >= cutoff)
    elif req.target == "inactive":
        cutoff = datetime.utcnow() - timedelta(days=7)
        query = query.where(User.updated_at < cutoff)

    if req.channel == "marketing":
        query = query.where(User.marketing_emails == True)

    users = (await db.execute(query)).scalars().all()
    sent, failed = 0, 0

    for user in users:
        try:
            if req.template:
                data = {
                    "subject": req.subject or "Update from kualia.ai",
                    "headline": req.subject or "Update from kualia.ai",
                    "body": req.body_html or "",
                    "cta_text": "Open kualia.ai",
                    "cta_url": "https://kualia.ai/dashboard",
                }
                result = await email_service.send_marketing(
                    to=user.email, template=req.template,
                    data=data, subject_override=req.subject, user_id=user.id,
                )
            else:
                if not req.subject or not req.body_html:
                    continue
                result = await email_service.send_raw(
                    to=user.email, subject=req.subject,
                    html=req.body_html, channel=req.channel, user_id=user.id,
                )
            if result.get("success"):
                sent += 1
            else:
                failed += 1
        except Exception as e:
            logger.warning("Failed to send to %s: %s", user.email, e)
            failed += 1

    return {"sent": sent, "failed": failed, "total_recipients": len(users)}


# ─── Admin: Email logs ───

@router.get("/logs")
async def email_logs(
    channel: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    _admin: dict = Depends(require_admin),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(EmailLog).order_by(desc(EmailLog.created_at))
    if channel:
        query = query.where(EmailLog.channel == channel)
    if status:
        query = query.where(EmailLog.status == status)

    total = (await db.execute(select(func.count(EmailLog.id)).where(
        (EmailLog.channel == channel) if channel else True,
        (EmailLog.status == status) if status else True,
    ))).scalar() or 0

    rows = (await db.execute(query.offset(offset).limit(limit))).scalars().all()
    return {
        "total": total,
        "logs": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "to_email": r.to_email,
                "subject": r.subject,
                "template": r.template,
                "channel": r.channel,
                "status": r.status,
                "resend_id": r.resend_id,
                "error": r.error,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }


# ─── Admin: Email stats ───

@router.get("/stats")
async def email_stats(db: AsyncSession = Depends(get_db), _admin: dict = Depends(require_admin)):
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)

    total_sent = (await db.execute(select(func.count(EmailLog.id)).where(EmailLog.status == "sent"))).scalar() or 0
    total_failed = (await db.execute(select(func.count(EmailLog.id)).where(EmailLog.status == "failed"))).scalar() or 0
    today_sent = (await db.execute(select(func.count(EmailLog.id)).where(
        EmailLog.status == "sent", EmailLog.created_at >= today
    ))).scalar() or 0
    week_sent = (await db.execute(select(func.count(EmailLog.id)).where(
        EmailLog.status == "sent", EmailLog.created_at >= week_ago
    ))).scalar() or 0

    transactional = (await db.execute(select(func.count(EmailLog.id)).where(EmailLog.channel == "transactional"))).scalar() or 0
    marketing = (await db.execute(select(func.count(EmailLog.id)).where(EmailLog.channel == "marketing"))).scalar() or 0

    return {
        "total_sent": total_sent,
        "total_failed": total_failed,
        "today_sent": today_sent,
        "week_sent": week_sent,
        "transactional": transactional,
        "marketing": marketing,
    }


# ─── Admin: Template preview ───

@router.get("/templates")
async def list_templates(_admin: dict = Depends(require_admin)):
    from app.services.email_service import TEMPLATES
    return {
        "templates": [
            {"name": k, "channel": "marketing" if k in ("new_feature", "tips_tricks", "reengagement") else "transactional"}
            for k in TEMPLATES.keys()
        ]
    }


@router.get("/templates/{name}/preview")
async def preview_template(name: str, _admin: dict = Depends(require_admin)):
    from app.services.email_service import TEMPLATES
    tpl = TEMPLATES.get(name)
    if not tpl:
        raise HTTPException(404, "Template not found")
    sample = {
        "env_name": "Drone Landing v2",
        "env_id": 42,
        "tests_passed": 8, "tests_total": 8,
        "domain": "robotics", "difficulty": "hard",
        "algorithm": "PPO", "timesteps": "500,000", "mean_reward": "187.3",
        "title": "Adaptive Multi-Agent Coordination in Dynamic Environments",
        "project_id": 7,
        "balance": "0.47",
        "subject": "New Feature: Continue Training & Curriculum Learning",
        "headline": "New Feature: Continue Training & Curriculum Learning",
        "body": "You can now continue training your agents with fine-tuning, curriculum learning, and advanced hyperparameter control.",
        "cta_text": "Try It Now",
        "cta_url": "https://kualia.ai/dashboard",
        "extra": "We've added curriculum learning and fine-tuning modes since your last visit.",
    }
    subject, html = tpl(sample)
    return {"name": name, "subject": subject, "html": html}


# ─── User: Email preferences ───

@router.put("/preferences")
async def update_email_preferences(
    req: EmailPrefsUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(
        select(User).where(User.clerk_id == current_user["clerk_user_id"])
    )).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    if req.email_notifications is not None:
        user.email_notifications = req.email_notifications
    if req.marketing_emails is not None:
        user.marketing_emails = req.marketing_emails

    await db.commit()
    return {
        "email_notifications": user.email_notifications,
        "marketing_emails": user.marketing_emails,
    }


@router.get("/preferences")
async def get_email_preferences(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(
        select(User).where(User.clerk_id == current_user["clerk_user_id"])
    )).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    return {
        "email_notifications": getattr(user, "email_notifications", True),
        "marketing_emails": getattr(user, "marketing_emails", True),
    }


# ─── Campaign management (admin) ───

@router.get("/campaigns")
async def list_campaigns(_admin: dict = Depends(require_admin)):
    from app.services.email_marketing_service import email_marketing_agent
    campaigns = await email_marketing_agent.get_campaigns()
    return {"campaigns": campaigns}


@router.post("/campaigns/generate-tips")
async def generate_tips(_admin: dict = Depends(require_admin)):
    from app.services.email_marketing_service import email_marketing_agent
    result = await email_marketing_agent.generate_tips_campaign()
    return result or {"error": "Generation failed"}


class FeatureRequest(BaseModel):
    description: str


@router.post("/campaigns/generate-feature")
async def generate_feature(req: FeatureRequest, _admin: dict = Depends(require_admin)):
    from app.services.email_marketing_service import email_marketing_agent
    result = await email_marketing_agent.generate_feature_campaign(req.description)
    return result or {"error": "Generation failed"}


@router.post("/campaigns/reengagement")
async def run_reengagement(_admin: dict = Depends(require_admin)):
    from app.services.email_marketing_service import email_marketing_agent
    result = await email_marketing_agent.run_reengagement_check()
    return result or {"error": "Check failed"}


@router.get("/campaigns/evaluate")
async def evaluate_performance(_admin: dict = Depends(require_admin)):
    from app.services.email_marketing_service import email_marketing_agent
    return await email_marketing_agent.evaluate_performance()


@router.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: int, db: AsyncSession = Depends(get_db), _admin: dict = Depends(require_admin)):
    from app.models import EmailCampaign
    from app.services.email_marketing_service import email_marketing_agent
    campaign = (await db.execute(
        select(EmailCampaign).where(EmailCampaign.id == campaign_id)
    )).scalar_one_or_none()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    return email_marketing_agent._serialize_campaign(campaign)


@router.get("/campaigns/{campaign_id}/preview")
async def preview_campaign(campaign_id: int, db: AsyncSession = Depends(get_db), _admin: dict = Depends(require_admin)):
    """Render the campaign as final HTML email for preview."""
    from app.models import EmailCampaign
    from app.services.email_service import TEMPLATES, _wrap_html, _btn, _badge, APP_URL
    campaign = (await db.execute(
        select(EmailCampaign).where(EmailCampaign.id == campaign_id)
    )).scalar_one_or_none()
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    tpl = TEMPLATES.get(campaign.campaign_type)
    if tpl:
        data = {
            "subject": campaign.subject,
            "headline": campaign.headline or campaign.subject,
            "body": campaign.body_html,
            "cta_text": campaign.cta_text or "Open kualia.ai",
            "cta_url": campaign.cta_url or f"{APP_URL}/dashboard",
            "extra": campaign.body_html,
            "unsubscribe_url": f"{APP_URL}/dashboard/settings",
        }
        subject, html = tpl(data)
    else:
        html = _wrap_html(campaign.body_html)
        subject = campaign.subject

    return {"subject": subject, "html": html}


@router.post("/campaigns/{campaign_id}/send")
async def send_campaign(campaign_id: int, _admin: dict = Depends(require_admin)):
    from app.services.email_marketing_service import email_marketing_agent
    return await email_marketing_agent._send_campaign(campaign_id)
