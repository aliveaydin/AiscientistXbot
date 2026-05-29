"""
Email Marketing Agent — AI-driven email campaign lifecycle.
Generates content, decides audience, sends campaigns, tracks performance,
and handles re-engagement flows autonomously.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models import User, EmailCampaign, EmailLog, SubscriptionPlan
from app.services.email_service import email_service, _wrap_html, _btn, _badge, APP_URL

logger = logging.getLogger("email_marketing_agent")

STYLE_GUIDE = """
HTML Style Guide for email body content:
- Use inline CSS only (no <style> blocks or classes)
- Structure: use <h2>, <h3> headings, <p> paragraphs, <ul>/<li> lists
- Spacing: every block element needs margin-bottom (16-24px)
- Typography: headings #111827, body text #4b5563, muted #9ca3af
- Highlight boxes: use <div> with background (#f0fdf4 green, #eff6ff blue, #fef3c7 amber, #f3f4f6 gray), border-radius:10px, padding:20px, border:1px solid matching color
- Numbered steps: use a <table> with number circles (small colored circles with numbers) and text
- Important terms: wrap in <strong> with color
- Use generous whitespace between sections (margin-bottom:24px on sections)
- Callout/tip boxes: colored left-border div (border-left:4px solid #color; padding-left:16px)
- Do NOT use <a> links in the body — the CTA button is added by the system separately
- Keep paragraphs short (2-3 sentences max per <p>)
- Line height: 1.7 on paragraphs for readability
"""

TIPS_SYSTEM_PROMPT = f"""You are the Email Marketing Agent for kualia.ai — an AI platform where users generate reinforcement learning environments from natural language, train agents, and write research papers.

Your job: write a valuable weekly email tip about reinforcement learning, environment design, or how to get the most out of kualia.ai.

Rules:
- Write in English
- 3-4 sections: an intro paragraph, a key insight box, an actionable how-to, and a closing thought
- Reference kualia.ai naturally (not pushy)
- Be genuinely helpful, educational, and professional
- The "body" field MUST be rich HTML — beautifully formatted with headings, highlight boxes, lists, and styled elements

{STYLE_GUIDE}

Output ONLY valid JSON:
{{"subject": "compelling email subject line", "headline": "short catchy headline", "body": "<h2>...</h2><p>...</p><div style=...>...</div>...", "cta_text": "action button text", "cta_url": "https://kualia.ai/dashboard"}}
"""

FEATURE_SYSTEM_PROMPT = f"""You are the Email Marketing Agent for kualia.ai. Write a compelling product update email announcing a new feature or improvement.

Platform context: kualia.ai lets users generate RL environments from text, train agents (PPO/SAC/A2C), run automated research pipelines with AI agents, and produce academic papers.

Rules:
- Write in English
- Structure: hero section with the feature name, what it does (with a highlight box), how to use it (numbered steps), and what's next
- Explain the benefit to the user, not just the feature
- The "body" field MUST be rich HTML — beautifully formatted with headings, highlight boxes, step-by-step sections, and styled elements

{STYLE_GUIDE}

Output ONLY valid JSON:
{{"subject": "compelling email subject line", "headline": "feature name or benefit", "body": "<h2>...</h2><p>...</p><div style=...>...</div>...", "cta_text": "action button text", "cta_url": "https://kualia.ai/dashboard"}}
"""

REENGAGEMENT_SYSTEM_PROMPT = f"""You are the Email Marketing Agent for kualia.ai. Write a friendly re-engagement email for users who haven't logged in for 7+ days.

Rules:
- Write in English
- Be warm, not guilt-tripping
- Mention what they might be missing (new features, community activity)
- Include a "what's new" highlights section with 2-3 items
- The "body" and "extra" fields MUST be rich HTML

{STYLE_GUIDE}

Output ONLY valid JSON:
{{"subject": "...", "headline": "...", "body": "<h2>...</h2><p>...</p>...", "extra": "<div style=...>highlights HTML</div>"}}
"""

CAMPAIGN_EVAL_PROMPT = """You are the analytics brain of kualia.ai's email marketing. Review these campaign metrics and decide what to do next.

Metrics:
{metrics}

Decide:
1. Should we send more tips, features, or re-engagement emails?
2. Which audience segments need attention?
3. Any campaigns to repeat or retire?

Output a brief JSON action plan: {{"next_campaign_type": "...", "target": "...", "reason": "...", "suggested_topic": "..."}}"""


class EmailMarketingAgent:
    def __init__(self):
        self._last_tip_topic = None

    async def generate_tips_campaign(self) -> Optional[dict]:
        """AI generates a weekly RL tip email, saves as campaign, and sends."""
        logger.info("[EmailAgent] Generating weekly tips campaign...")
        try:
            from app.services.ai_service import ai_service

            user_prompt = (
                f"Write a weekly RL tip email. Today is {datetime.utcnow().strftime('%B %d, %Y')}. "
                f"Previous topic was: {self._last_tip_topic or 'none yet'}. Pick a different topic."
            )
            raw = await ai_service._call_ai(TIPS_SYSTEM_PROMPT, user_prompt, max_tokens=4000)
            data = self._parse_json(raw)
            if not data or not data.get("body"):
                logger.warning("[EmailAgent] Tips generation returned invalid data")
                return None

            self._last_tip_topic = data.get("headline", "")

            campaign = await self._save_campaign(
                name=f"Weekly Tip: {data.get('headline', 'RL Tip')[:80]}",
                campaign_type="tips_tricks",
                subject=data.get("subject", "RL Tip of the Week"),
                headline=data.get("headline", ""),
                body_html=data.get("body", ""),
                cta_text=data.get("cta_text", "Try It on kualia.ai"),
                cta_url=data.get("cta_url", f"{APP_URL}/dashboard"),
                target_audience="all",
                ai_generated=True,
                ai_rationale=f"Auto-generated weekly tip about: {data.get('headline', '')}",
            )
            if campaign:
                result = await self._send_campaign(campaign.id)
                return result
        except Exception as e:
            logger.error("[EmailAgent] Tips campaign failed: %s", e)
        return None

    async def generate_feature_campaign(self, feature_description: str) -> Optional[dict]:
        """AI writes a feature announcement email from a description."""
        logger.info("[EmailAgent] Generating feature announcement: %s", feature_description[:80])
        try:
            from app.services.ai_service import ai_service
            raw = await ai_service._call_ai(
                FEATURE_SYSTEM_PROMPT,
                f"Write an email about this new feature:\n{feature_description}",
                max_tokens=4000,
            )
            data = self._parse_json(raw)
            if not data:
                return None

            campaign = await self._save_campaign(
                name=f"Feature: {data.get('headline', feature_description[:60])}",
                campaign_type="new_feature",
                subject=data.get("subject", "New on kualia.ai"),
                headline=data.get("headline", ""),
                body_html=data.get("body", ""),
                cta_text=data.get("cta_text", "Try It Now"),
                cta_url=data.get("cta_url", f"{APP_URL}/dashboard"),
                target_audience="all",
                ai_generated=True,
                ai_rationale=f"Feature announcement: {feature_description[:200]}",
            )
            if campaign:
                return await self._send_campaign(campaign.id)
        except Exception as e:
            logger.error("[EmailAgent] Feature campaign failed: %s", e)
        return None

    async def run_reengagement_check(self) -> Optional[dict]:
        """Find inactive users (7+ days) and send re-engagement emails."""
        logger.info("[EmailAgent] Running re-engagement check...")
        try:
            cutoff = datetime.utcnow() - timedelta(days=7)
            recent_reengagement = datetime.utcnow() - timedelta(days=14)

            async with async_session() as db:
                # Users inactive for 7+ days who opted in to marketing
                inactive = (await db.execute(
                    select(User).where(
                        User.updated_at < cutoff,
                        User.email.isnot(None),
                        User.marketing_emails == True,
                    )
                )).scalars().all()

                if not inactive:
                    logger.info("[EmailAgent] No inactive users found")
                    return {"sent": 0, "reason": "no_inactive_users"}

                # Don't spam: check who already received reengagement recently
                already_sent = set()
                recent_logs = (await db.execute(
                    select(EmailLog.to_email).where(
                        EmailLog.template == "reengagement",
                        EmailLog.created_at >= recent_reengagement,
                    )
                )).scalars().all()
                already_sent = set(recent_logs)

                targets = [u for u in inactive if u.email not in already_sent]
                if not targets:
                    logger.info("[EmailAgent] All inactive users already contacted recently")
                    return {"sent": 0, "reason": "already_contacted"}

            # Generate personalized content via AI
            from app.services.ai_service import ai_service
            raw = await ai_service._call_ai(
                REENGAGEMENT_SYSTEM_PROMPT,
                f"Write a re-engagement email. We have {len(targets)} users who haven't visited in 7+ days.",
                max_tokens=4000,
            )
            data = self._parse_json(raw)
            extra = data.get("extra", "") if data else ""

            sent, failed = 0, 0
            for user in targets[:50]:  # cap at 50 per run
                try:
                    result = await email_service.send_marketing(
                        to=user.email, template="reengagement",
                        data={"extra": extra},
                        user_id=user.id,
                    )
                    if result.get("success"):
                        sent += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1

            logger.info("[EmailAgent] Re-engagement: sent=%d, failed=%d, pool=%d", sent, failed, len(targets))
            return {"sent": sent, "failed": failed, "pool": len(targets)}
        except Exception as e:
            logger.error("[EmailAgent] Re-engagement failed: %s", e)
            return None

    async def evaluate_performance(self) -> dict:
        """Analyze campaign metrics and decide next actions."""
        logger.info("[EmailAgent] Running campaign performance evaluation...")
        try:
            async with async_session() as db:
                week_ago = datetime.utcnow() - timedelta(days=7)
                total_sent = (await db.execute(
                    select(func.count(EmailLog.id)).where(EmailLog.status == "sent", EmailLog.created_at >= week_ago)
                )).scalar() or 0
                total_failed = (await db.execute(
                    select(func.count(EmailLog.id)).where(EmailLog.status == "failed", EmailLog.created_at >= week_ago)
                )).scalar() or 0
                by_template = {}
                for tpl in ["welcome", "training_complete", "paper_ready", "env_ready", "credits_low", "reengagement", "tips_tricks", "new_feature"]:
                    count = (await db.execute(
                        select(func.count(EmailLog.id)).where(EmailLog.template == tpl, EmailLog.created_at >= week_ago)
                    )).scalar() or 0
                    by_template[tpl] = count

                campaigns = (await db.execute(
                    select(EmailCampaign).where(EmailCampaign.created_at >= week_ago).order_by(desc(EmailCampaign.created_at))
                )).scalars().all()
                campaign_summaries = [
                    {"name": c.name, "type": c.campaign_type, "sent": c.sent_count, "failed": c.failed_count, "status": c.status}
                    for c in campaigns
                ]

            metrics = {
                "period": "last 7 days",
                "total_sent": total_sent,
                "total_failed": total_failed,
                "by_template": by_template,
                "campaigns": campaign_summaries,
            }

            from app.services.ai_service import ai_service
            raw = await ai_service._call_ai(
                CAMPAIGN_EVAL_PROMPT.format(metrics=json.dumps(metrics, indent=2)),
                "Analyze and give your action plan.",
                max_tokens=500,
            )
            plan = self._parse_json(raw)

            result = {"metrics": metrics, "action_plan": plan}
            logger.info("[EmailAgent] Evaluation complete: %s", json.dumps(plan or {}, default=str)[:300])
            return result
        except Exception as e:
            logger.error("[EmailAgent] Evaluation failed: %s", e)
            return {"error": str(e)}

    async def get_campaigns(self, limit: int = 20) -> List[dict]:
        """List recent campaigns."""
        async with async_session() as db:
            rows = (await db.execute(
                select(EmailCampaign).order_by(desc(EmailCampaign.created_at)).limit(limit)
            )).scalars().all()
            return [self._serialize_campaign(c) for c in rows]

    def _serialize_campaign(self, c) -> dict:
        return {
            "id": c.id, "name": c.name, "type": c.campaign_type,
            "subject": c.subject, "headline": c.headline,
            "body_html": c.body_html, "cta_text": c.cta_text, "cta_url": c.cta_url,
            "status": c.status, "target": c.target_audience,
            "ai_generated": c.ai_generated, "ai_rationale": c.ai_rationale,
            "sent_count": c.sent_count, "failed_count": c.failed_count,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "sent_at": c.sent_at.isoformat() if c.sent_at else None,
        }

    async def _save_campaign(self, **kwargs) -> Optional[EmailCampaign]:
        try:
            async with async_session() as db:
                campaign = EmailCampaign(**kwargs)
                db.add(campaign)
                await db.commit()
                await db.refresh(campaign)
                return campaign
        except Exception as e:
            logger.error("[EmailAgent] Failed to save campaign: %s", e)
            return None

    async def _send_campaign(self, campaign_id: int) -> dict:
        """Execute a campaign: send to all matching users."""
        async with async_session() as db:
            campaign = (await db.execute(
                select(EmailCampaign).where(EmailCampaign.id == campaign_id)
            )).scalar_one_or_none()
            if not campaign:
                return {"error": "Campaign not found"}
            if campaign.status == "sent":
                return {"error": "Campaign already sent"}

            campaign.status = "sending"
            await db.commit()

            query = select(User).where(User.email.isnot(None), User.marketing_emails == True)
            target = campaign.target_audience
            if target in ("free", "starter", "pro", "lab"):
                sub = select(SubscriptionPlan.id).where(SubscriptionPlan.name == target)
                query = query.where(User.plan_id.in_(sub))
            elif target == "active":
                query = query.where(User.updated_at >= datetime.utcnow() - timedelta(days=7))
            elif target == "inactive":
                query = query.where(User.updated_at < datetime.utcnow() - timedelta(days=7))

            users = (await db.execute(query)).scalars().all()

        sent, failed = 0, 0
        template = campaign.campaign_type if campaign.campaign_type in ("new_feature", "tips_tricks", "reengagement") else None

        for user in users:
            try:
                if template:
                    result = await email_service.send_marketing(
                        to=user.email, template=template,
                        data={
                            "subject": campaign.subject,
                            "headline": campaign.headline or campaign.subject,
                            "body": campaign.body_html,
                            "cta_text": campaign.cta_text or "Open kualia.ai",
                            "cta_url": campaign.cta_url or f"{APP_URL}/dashboard",
                        },
                        subject_override=campaign.subject,
                        user_id=user.id,
                    )
                else:
                    result = await email_service.send_raw(
                        to=user.email, subject=campaign.subject,
                        html=campaign.body_html, channel="marketing", user_id=user.id,
                    )
                if result.get("success"):
                    sent += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

        async with async_session() as db:
            campaign = (await db.execute(
                select(EmailCampaign).where(EmailCampaign.id == campaign_id)
            )).scalar_one_or_none()
            if campaign:
                campaign.status = "sent"
                campaign.sent_count = sent
                campaign.failed_count = failed
                campaign.sent_at = datetime.utcnow()
                await db.commit()

        logger.info("[EmailAgent] Campaign #%d sent: %d/%d", campaign_id, sent, sent + failed)
        return {"campaign_id": campaign_id, "sent": sent, "failed": failed, "total": len(users)}

    def _parse_json(self, raw: str) -> Optional[dict]:
        import re
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        # Try direct parse first
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = raw[start:end]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # Fallback: field-by-field extraction using key positions
        try:
            text = raw[start:] if start >= 0 else raw
            result = {}
            fields = ["subject", "headline", "body", "extra", "cta_text", "cta_url"]

            for field in fields:
                key_pattern = f'"{field}"\\s*:\\s*"'
                m = re.search(key_pattern, text)
                if not m:
                    continue
                val_start = m.end()

                # Walk forward finding the true end of the value string
                # (handling escaped quotes inside)
                i = val_start
                depth = 0
                while i < len(text):
                    ch = text[i]
                    if ch == '\\':
                        i += 2
                        continue
                    if ch == '"':
                        # Check if next non-whitespace is , or } (end of value)
                        rest = text[i+1:].lstrip()
                        if not rest or rest[0] in ',}':
                            result[field] = text[val_start:i].replace('\\"', '"').replace('\\n', '\n')
                            break
                    i += 1

            if result.get("body") or result.get("extra") or result.get("subject"):
                logger.info("[EmailAgent] Parsed JSON via field extraction (%d fields: %s)", len(result), list(result.keys()))
                return result
        except Exception as e:
            logger.warning("[EmailAgent] Field extraction failed: %s", e)

        logger.warning("[EmailAgent] Failed to parse JSON from AI response: %s", raw[:300])
        return None


email_marketing_agent = EmailMarketingAgent()
