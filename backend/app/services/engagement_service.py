"""
GTM Engineering Agent — User Acquisition Engine for kualia.ai

Strategies:
1. Prospect Detection: Find RL researchers/students who'd benefit from kualia.ai
2. Value-Add Replies: Reply to RL questions with genuine help + subtle kualia.ai mention
3. Strategic Likes: Like tweets from high-value prospects to get noticed
4. Follow Targets: Follow key RL accounts to build network
5. Conversion Tracking: Track prospect journey from detected → engaged → warm → converted
"""
import logging
import random
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import EngagementLog, Prospect
from app.services.twitter_service import kualia_twitter_service
from app.services.ai_service import ai_service
from app.config import settings

logger = logging.getLogger("gtm_agent")

# --- Search Strategies ---

PROSPECT_QUERIES = [
    '"building RL environment" -is:retweet',
    '"gymnasium custom" -is:retweet',
    '"custom gym environment" -is:retweet',
    '"reinforcement learning project" -is:retweet',
    '"RL environment" help OR how OR build OR create -is:retweet',
    '"stable baselines" training OR agent -is:retweet',
    '"reward function" design OR shaping -is:retweet',
    '"RL paper" writing OR research -is:retweet',
    '"PPO training" OR "SAC training" results -is:retweet',
    '"openai gym" custom OR build -is:retweet',
    '"reinforcement learning" beginner OR learning OR started -is:retweet',
    '"RL research" lab OR university -is:retweet',
]

AUTHORITY_QUERIES = [
    '"reinforcement learning" min_faves:50 -is:retweet',
    '"RL environment" min_faves:20 -is:retweet',
    '"gymnasium" min_faves:20 -is:retweet',
]

DAILY_LIKE_LIMIT = 30
DAILY_REPLY_LIMIT = 4
MAX_LIKES_PER_USER_PER_DAY = 2

# --- AI Prompts ---

PROSPECT_SCORER_PROMPT = """You are a sales qualification AI for kualia.ai, an RL environment generation and 
training platform. Analyze this Twitter user's tweet and determine how likely they are to benefit from kualia.ai.

Score from 0-100:
- 90-100: They're actively struggling with RL environment creation, training, or research paper writing
- 70-89: They work in RL/ML and would clearly benefit from automated env generation
- 50-69: They're in the ML space and might find kualia.ai useful
- 30-49: Tangentially related to RL/ML
- 0-29: Not a good prospect

Also provide tags (comma-separated): researcher, student, professor, industry, hobbyist, lab

Respond in JSON only: {"score": N, "tags": "tag1,tag2", "reason": "one sentence why"}
"""

VALUE_REPLY_PROMPT = """You are the kualia.ai Twitter account. Your goal is to be genuinely helpful to someone 
in the RL/ML community. Their tweet suggests they might benefit from kualia.ai.

Write a reply that:
1. DIRECTLY addresses their specific question/problem with real technical insight
2. Positions kualia.ai as a relevant solution ONLY if it genuinely fits their need
3. Sounds like a knowledgeable colleague, NOT a sales pitch

Rules:
- 150-270 characters. Finish your sentences.
- Lead with value. The help comes first, kualia.ai mention comes naturally (or not at all).
- If they're asking about env design: mention kualia.ai generates custom Gymnasium envs from descriptions
- If they're struggling with training: mention kualia.ai handles PPO/SAC/DQN training with hyperparameter config
- If they're writing a paper: mention kualia.ai auto-generates research papers from training results
- If it's a general RL question: just answer it well, maybe add "we've been working on this at kualia.ai"
- NEVER be pushy. NEVER say "check out" or "try" as first words.
"""

QUOTE_TWEET_PROMPT = """You are the kualia.ai Twitter account. Write a quote-tweet comment that adds 
unique insight to an interesting RL/ML tweet. Show your expertise while subtly establishing kualia.ai's authority.

Rules:
- 100-200 characters. Thoughtful, technical, adds value.
- Don't just agree — add a new angle, a "what if", or practical experience.
- Mention kualia.ai only if directly relevant to the point you're making.
"""


class EngagementService:
    """GTM Engineering Agent — strategic user acquisition for kualia.ai."""

    def __init__(self):
        self.override_queries = None  # set by strategy engine for targeted sessions

    # -------------------------------------------------------
    # 1. PROSPECT DETECTION
    # -------------------------------------------------------
    async def discover_prospects(self, db: AsyncSession, max_results: int = 20) -> Dict:
        """Search Twitter for potential kualia.ai users and score them."""
        pool = self.override_queries if self.override_queries else PROSPECT_QUERIES
        query = random.choice(pool)
        logger.info("Prospect discovery: searching '%s'", query)

        tweets = await kualia_twitter_service.search_tweets(query, max_results=max_results)
        if not tweets:
            return {"discovered": 0, "query": query}

        discovered = 0
        for tweet in tweets:
            username = tweet.get("author_username", "")
            if not username:
                continue

            existing = await db.execute(
                select(Prospect).where(Prospect.twitter_username == username)
            )
            if existing.scalar_one_or_none():
                continue

            score_data = await self._score_prospect(tweet.get("text", ""))

            prospect = Prospect(
                twitter_username=username,
                display_name=username,
                score=score_data.get("score", 30),
                tags=score_data.get("tags", ""),
                stage="detected",
                first_seen_tweet=tweet.get("text", "")[:500],
                notes=score_data.get("reason", ""),
            )
            db.add(prospect)

            db.add(EngagementLog(
                action_type="prospect_detect",
                target_username=username,
                target_tweet_id=tweet.get("id"),
                target_text=tweet.get("text", "")[:500],
                search_query=query,
                status="completed",
            ))
            discovered += 1

        await db.commit()
        logger.info("Discovered %d new prospects from '%s'", discovered, query)
        return {"discovered": discovered, "query": query, "total_searched": len(tweets)}

    async def _score_prospect(self, tweet_text: str) -> Dict:
        """Use AI to score a prospect based on their tweet."""
        try:
            user_prompt = f"Tweet: \"{tweet_text}\"\n\nScore this person as a kualia.ai prospect."
            raw = await ai_service._call_ai(PROSPECT_SCORER_PROMPT, user_prompt, max_tokens=200)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1].replace("json", "").strip()
            return json.loads(raw)
        except Exception as e:
            logger.warning("Prospect scoring failed: %s", e)
            return {"score": 30, "tags": "unknown", "reason": "scoring failed"}

    # -------------------------------------------------------
    # 2. STRATEGIC ENGAGEMENT (Like + Reply)
    # -------------------------------------------------------
    async def engage_prospects(self, db: AsyncSession, max_actions: int = 15) -> Dict:
        """Multi-action engagement: like high-value tweets AND generate reply suggestions."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        today_likes = (await db.execute(
            select(func.count(EngagementLog.id)).where(
                EngagementLog.action_type == "like",
                EngagementLog.created_at >= today_start,
            )
        )).scalar() or 0

        today_replies = (await db.execute(
            select(func.count(EngagementLog.id)).where(
                EngagementLog.action_type.in_(["reply", "reply_suggestion"]),
                EngagementLog.created_at >= today_start,
            )
        )).scalar() or 0

        like_budget = min(DAILY_LIKE_LIMIT - today_likes, max_actions)
        reply_budget = min(DAILY_REPLY_LIMIT - today_replies, 2)

        pool = self.override_queries if self.override_queries else PROSPECT_QUERIES
        query = random.choice(pool)
        tweets = await kualia_twitter_service.search_tweets(query, max_results=25)
        if not tweets:
            return {"liked": 0, "reply_suggestions": 0, "query": query}

        user_like_counts = await self._get_user_like_counts(db, today_start)

        liked = 0
        reply_suggestions = 0

        for tweet in tweets:
            if liked >= like_budget and reply_suggestions >= reply_budget:
                break

            username = tweet.get("author_username", "")
            tweet_id = tweet.get("id", "")
            tweet_text = tweet.get("text", "")

            if user_like_counts.get(username, 0) >= MAX_LIKES_PER_USER_PER_DAY:
                continue

            already = await db.execute(
                select(EngagementLog.id).where(
                    EngagementLog.target_tweet_id == tweet_id,
                    EngagementLog.action_type.in_(["like", "reply", "reply_suggestion"]),
                )
            )
            if already.scalar_one_or_none():
                continue

            if liked < like_budget:
                result = await kualia_twitter_service.like_tweet(tweet_id)
                db.add(EngagementLog(
                    action_type="like",
                    target_tweet_id=tweet_id,
                    target_username=username,
                    target_text=tweet_text[:500],
                    search_query=query,
                    status="completed" if result.get("success") else "failed",
                ))
                if result.get("success"):
                    liked += 1
                    user_like_counts[username] = user_like_counts.get(username, 0) + 1
                    await self._update_prospect_interaction(db, username, tweet_text)

            metrics = tweet.get("metrics", {})
            engagement_count = (metrics.get("like_count", 0) + metrics.get("reply_count", 0))
            is_question = any(w in tweet_text.lower() for w in [
                "how do", "how to", "anyone know", "struggling with", "help with",
                "?", "looking for", "need a", "recommend", "advice",
                "build", "create", "train", "environment",
            ])

            if reply_suggestions < reply_budget and is_question:
                suggestion = await self._generate_value_reply(tweet_text)
                db.add(EngagementLog(
                    action_type="reply_suggestion",
                    target_tweet_id=tweet_id,
                    target_username=username,
                    target_text=tweet_text[:500],
                    search_query=query,
                    reply_suggestion=suggestion,
                    status="pending_approval",
                ))
                reply_suggestions += 1
                logger.info("Reply suggestion for @%s: %s", username, suggestion[:60])

        await db.commit()
        return {
            "liked": liked,
            "reply_suggestions": reply_suggestions,
            "query": query,
            "total_searched": len(tweets),
        }

    async def _generate_value_reply(self, tweet_text: str) -> str:
        """Generate a helpful reply that positions kualia.ai naturally."""
        user_prompt = f"Their tweet:\n\"{tweet_text}\"\n\nWrite a helpful reply."
        try:
            reply = await ai_service._call_ai(VALUE_REPLY_PROMPT, user_prompt, max_tokens=400)
            reply = reply.strip()
            if reply.startswith('"') and reply.endswith('"'):
                reply = reply[1:-1]
            return reply
        except Exception as e:
            logger.error("Reply generation failed: %s", e)
            return ""

    async def _update_prospect_interaction(self, db: AsyncSession, username: str, tweet_text: str):
        """Update prospect record when we interact with them."""
        result = await db.execute(
            select(Prospect).where(Prospect.twitter_username == username)
        )
        prospect = result.scalar_one_or_none()
        if prospect:
            prospect.total_interactions += 1
            prospect.last_interaction_at = datetime.utcnow()
            if prospect.stage == "detected":
                prospect.stage = "engaged"
        else:
            prospect = Prospect(
                twitter_username=username,
                display_name=username,
                score=40,
                stage="engaged",
                first_seen_tweet=tweet_text[:500],
                total_interactions=1,
                last_interaction_at=datetime.utcnow(),
            )
            db.add(prospect)

    async def _get_user_like_counts(self, db: AsyncSession, since: datetime) -> Dict[str, int]:
        result = await db.execute(
            select(EngagementLog.target_username).where(
                EngagementLog.action_type == "like",
                EngagementLog.created_at >= since,
            )
        )
        counts: Dict[str, int] = {}
        for row in result.fetchall():
            uname = row[0] or ""
            counts[uname] = counts.get(uname, 0) + 1
        return counts

    # -------------------------------------------------------
    # 3. REPLY MANAGEMENT (Admin approves, system posts)
    # -------------------------------------------------------
    async def post_approved_reply(self, log_id: int, db: AsyncSession) -> Dict:
        """Post an admin-approved reply suggestion to Twitter."""
        result = await db.execute(
            select(EngagementLog).where(EngagementLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        if not log or log.action_type != "reply_suggestion":
            return {"success": False, "error": "Not a reply suggestion"}
        if log.status != "pending_approval":
            return {"success": False, "error": f"Status is {log.status}, not pending_approval"}

        post_result = await kualia_twitter_service.post_reply(
            log.reply_suggestion,
            log.target_tweet_id,
            db,
        )
        if post_result.get("success"):
            log.status = "completed"
            log.action_type = "reply"
            await self._update_prospect_interaction(db, log.target_username or "", log.target_text or "")
            await db.commit()
            return {"success": True, "reply_id": post_result.get("reply_id")}
        else:
            log.status = "failed"
            await db.commit()
            return {"success": False, "error": post_result.get("error", "Unknown")}

    async def reject_reply(self, log_id: int, db: AsyncSession) -> Dict:
        """Admin rejects a reply suggestion."""
        result = await db.execute(
            select(EngagementLog).where(EngagementLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        if not log:
            return {"success": False, "error": "Not found"}
        log.status = "rejected"
        await db.commit()
        return {"success": True}

    # -------------------------------------------------------
    # 4. PROSPECT PIPELINE
    # -------------------------------------------------------
    async def get_prospects(self, db: AsyncSession, stage: Optional[str] = None,
                            min_score: int = 0, limit: int = 50) -> List[Dict]:
        """Get prospect list with optional filters."""
        query = select(Prospect).order_by(Prospect.score.desc()).limit(limit)
        if stage:
            query = query.where(Prospect.stage == stage)
        if min_score > 0:
            query = query.where(Prospect.score >= min_score)

        result = await db.execute(query)
        prospects = result.scalars().all()

        return [
            {
                "id": p.id,
                "twitter_username": p.twitter_username,
                "display_name": p.display_name,
                "score": p.score,
                "tags": p.tags,
                "stage": p.stage,
                "first_seen_tweet": p.first_seen_tweet,
                "total_interactions": p.total_interactions,
                "last_interaction_at": p.last_interaction_at.isoformat() if p.last_interaction_at else None,
                "notes": p.notes,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in prospects
        ]

    async def get_prospect_funnel(self, db: AsyncSession) -> Dict:
        """Get prospect conversion funnel stats."""
        stages = ["detected", "engaged", "warm", "converted", "disqualified"]
        funnel = {}
        for stage in stages:
            count = (await db.execute(
                select(func.count(Prospect.id)).where(Prospect.stage == stage)
            )).scalar() or 0
            funnel[stage] = count

        total = (await db.execute(select(func.count(Prospect.id)))).scalar() or 0
        avg_score = (await db.execute(select(func.avg(Prospect.score)))).scalar() or 0
        high_value = (await db.execute(
            select(func.count(Prospect.id)).where(Prospect.score >= 70)
        )).scalar() or 0

        return {
            "funnel": funnel,
            "total_prospects": total,
            "avg_score": round(avg_score, 1),
            "high_value_count": high_value,
        }

    async def update_prospect_stage(self, prospect_id: int, stage: str, db: AsyncSession) -> Dict:
        result = await db.execute(select(Prospect).where(Prospect.id == prospect_id))
        prospect = result.scalar_one_or_none()
        if not prospect:
            return {"success": False, "error": "Prospect not found"}
        prospect.stage = stage
        await db.commit()
        return {"success": True, "username": prospect.twitter_username, "stage": stage}

    # -------------------------------------------------------
    # 5. STATS & ANALYTICS
    # -------------------------------------------------------
    async def get_engagement_stats(self, db: AsyncSession, days: int = 7) -> Dict:
        since = datetime.utcnow() - timedelta(days=days)

        total_likes = (await db.execute(
            select(func.count(EngagementLog.id)).where(
                EngagementLog.action_type == "like",
                EngagementLog.status == "completed",
                EngagementLog.created_at >= since,
            )
        )).scalar() or 0

        total_replies = (await db.execute(
            select(func.count(EngagementLog.id)).where(
                EngagementLog.action_type == "reply",
                EngagementLog.created_at >= since,
            )
        )).scalar() or 0

        total_suggestions = (await db.execute(
            select(func.count(EngagementLog.id)).where(
                EngagementLog.action_type == "reply_suggestion",
                EngagementLog.created_at >= since,
            )
        )).scalar() or 0

        pending_replies = (await db.execute(
            select(func.count(EngagementLog.id)).where(
                EngagementLog.action_type == "reply_suggestion",
                EngagementLog.status == "pending_approval",
            )
        )).scalar() or 0

        new_prospects = (await db.execute(
            select(func.count(Prospect.id)).where(Prospect.created_at >= since)
        )).scalar() or 0

        daily_breakdown = []
        for day_offset in range(days):
            day_start = (datetime.utcnow() - timedelta(days=day_offset)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end = day_start + timedelta(days=1)
            likes = (await db.execute(
                select(func.count(EngagementLog.id)).where(
                    EngagementLog.action_type == "like",
                    EngagementLog.status == "completed",
                    EngagementLog.created_at >= day_start,
                    EngagementLog.created_at < day_end,
                )
            )).scalar() or 0
            replies = (await db.execute(
                select(func.count(EngagementLog.id)).where(
                    EngagementLog.action_type == "reply",
                    EngagementLog.created_at >= day_start,
                    EngagementLog.created_at < day_end,
                )
            )).scalar() or 0
            daily_breakdown.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "likes": likes,
                "replies": replies,
            })

        return {
            "total_likes": total_likes,
            "total_replies": total_replies,
            "total_reply_suggestions": total_suggestions,
            "pending_replies": pending_replies,
            "new_prospects": new_prospects,
            "daily_breakdown": list(reversed(daily_breakdown)),
        }

    async def get_recent_logs(self, db: AsyncSession, limit: int = 50,
                              action_type: Optional[str] = None) -> List[Dict]:
        query = select(EngagementLog).order_by(EngagementLog.created_at.desc()).limit(limit)
        if action_type:
            query = query.where(EngagementLog.action_type == action_type)

        result = await db.execute(query)
        logs = result.scalars().all()

        return [
            {
                "id": log.id,
                "action_type": log.action_type,
                "target_tweet_id": log.target_tweet_id,
                "target_username": log.target_username,
                "target_text": log.target_text,
                "search_query": log.search_query,
                "reply_suggestion": log.reply_suggestion,
                "status": log.status,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]

    # Legacy alias
    async def search_and_like(self, db: AsyncSession, max_likes: int = 10) -> Dict:
        return await self.engage_prospects(db, max_actions=max_likes)

    async def generate_reply_suggestion(self, tweet_text: str, tweet_id: str, db: AsyncSession) -> Dict:
        suggestion = await self._generate_value_reply(tweet_text)
        log = EngagementLog(
            action_type="reply_suggestion",
            target_tweet_id=tweet_id,
            target_text=tweet_text[:500],
            reply_suggestion=suggestion,
            status="pending_approval",
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return {"id": log.id, "tweet_id": tweet_id, "tweet_text": tweet_text, "suggestion": suggestion}


engagement_service = EngagementService()
