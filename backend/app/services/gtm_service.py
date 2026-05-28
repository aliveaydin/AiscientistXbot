"""
Go-To-Market (GTM) Agent Service for kualia.ai marketing.
Generates marketing tweets across 4 content categories with visual content.
"""
import logging
import random
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import MarketingTweet, EngagementLog, Prospect, GTMReport, RLEnvironment, TrainingRun, ResearchPaper
from app.services.ai_service import ai_service
from app.config import settings

logger = logging.getLogger("gtm_service")

CONTENT_TYPES = ["product", "industry", "educational", "showcase"]

HASHTAG_POOL = [
    "#ReinforcementLearning", "#RL", "#Gymnasium", "#MachineLearning",
    "#AI", "#AgentTraining", "#RLEnvironment", "#DeepRL",
    "#ArtificialIntelligence", "#MLResearch", "#OpenAI", "#StableBaselines3",
]

PRODUCT_SYSTEM_PROMPT = """You are the marketing voice of kualia.ai — a platform that lets researchers 
generate custom RL environments with AI, train agents, run experiments, and produce academic papers automatically.

Write a compelling tweet about a kualia.ai feature or use case. Be specific, technical enough 
to impress ML practitioners, yet accessible. Sound like a passionate engineer, not a corporate account.

Rules:
- 200-500 characters. NEVER exceed 600.
- No emojis unless they add genuine meaning (one max).
- Include a subtle CTA or mention kualia.ai naturally.
- ALWAYS finish your sentences.
- Do NOT use quotation marks around the entire tweet.
- Write in English.
"""

INDUSTRY_SYSTEM_PROMPT = """You are an RL/AI thought leader who also happens to build kualia.ai.
Comment on a recent RL trend, research direction, or industry development.
Be insightful and offer a unique perspective. You may reference kualia.ai briefly if relevant,
but the primary value is the insight itself.

Rules:
- 200-500 characters. NEVER exceed 600.
- Sound knowledgeable and opinionated (in a good way).
- No emojis unless they add genuine meaning (one max).
- ALWAYS finish your sentences.
- Do NOT use quotation marks around the entire tweet.
- Write in English.
"""

EDUCATIONAL_SYSTEM_PROMPT = """You are an RL educator building kualia.ai. Share a useful RL concept, 
tip, comparison, or practical insight. Help people learn something in a single tweet.

Rules:
- 200-500 characters. NEVER exceed 600.
- Be concrete with examples when possible.
- Mention kualia.ai only if it naturally fits the educational point.
- No emojis unless they add genuine meaning (one max).
- ALWAYS finish your sentences.
- Do NOT use quotation marks around the entire tweet.
- Write in English.
"""

SHOWCASE_SYSTEM_PROMPT = """You are showing off real results from kualia.ai. Given environment/training data,
write a tweet that showcases what the platform can produce. Be specific with numbers and results.

Rules:
- 200-500 characters. NEVER exceed 600.
- Include specific metrics when available (reward, steps, success rate).
- Sound excited but authentic.
- No emojis unless they add genuine meaning (one max).
- ALWAYS finish your sentences.
- Do NOT use quotation marks around the entire tweet.
- Write in English.
"""

SYSTEM_PROMPTS = {
    "product": PRODUCT_SYSTEM_PROMPT,
    "industry": INDUSTRY_SYSTEM_PROMPT,
    "educational": EDUCATIONAL_SYSTEM_PROMPT,
    "showcase": SHOWCASE_SYSTEM_PROMPT,
}

PRODUCT_TOPICS = [
    "AI-powered environment generation from natural language descriptions",
    "Curriculum learning: train on easy envs first, auto-increase difficulty",
    "Fine-tune mode: low learning rate on pre-trained agent for precision",
    "One-click research paper generation from training results",
    "Hypothesis-first research pipeline: describe your idea, get a full paper",
    "Supported algorithms: PPO, SAC, DQN with hyperparameter configuration",
    "Builder chat: iterate on your environment design with AI assistance",
    "Export trained agents and environments to GitHub",
    "Real training curves, evaluation episodes, and reproducibility stats in papers",
    "Template environments: gridworld, trading, cartpole, inventory, drone navigation",
    "Multi-domain support: robotics, finance, game, control, optimization, healthcare",
]

INDUSTRY_TOPICS = [
    "The shift from hand-crafted to AI-generated RL environments",
    "Why curriculum learning is becoming essential for complex RL tasks",
    "The gap between RL research papers and reproducible results",
    "How automated experiment pipelines are changing ML research velocity",
    "The role of environment design in agent generalization",
    "PPO vs SAC: when to use which algorithm and why",
    "Why most RL papers lack proper ablation studies",
    "The future of automated scientific discovery with AI agents",
    "Sim-to-real transfer: why environment fidelity matters",
    "Meta-learning and adaptive agents in dynamic environments",
]

EDUCATIONAL_TOPICS = [
    "What is observation space in RL and why it matters for agent learning",
    "Reward shaping: how to design rewards that actually work",
    "The exploration-exploitation tradeoff explained simply",
    "Why PPO uses clipped surrogate objectives (and what that means)",
    "Continuous vs discrete action spaces: practical differences",
    "What happens when your RL agent's training curve plateaus",
    "The importance of environment reset and episode structure",
    "How discount factor (gamma) affects long-term vs short-term planning",
    "Why normalizing observations improves training stability",
    "Experience replay: how agents learn from past mistakes",
]


class GTMService:
    """Generates marketing content for kualia.ai across multiple content types."""

    async def generate_gtm_tweet(
        self,
        content_type: str,
        db: AsyncSession,
        custom_topic: Optional[str] = None,
    ) -> MarketingTweet:
        if content_type not in CONTENT_TYPES:
            content_type = random.choice(CONTENT_TYPES)

        system_prompt = SYSTEM_PROMPTS[content_type]
        user_prompt = await self._build_user_prompt(content_type, db, custom_topic)

        tweet_text = await ai_service._call_ai(system_prompt, user_prompt, max_tokens=800)

        if tweet_text.startswith('"') and tweet_text.endswith('"'):
            tweet_text = tweet_text[1:-1]
        tweet_text = tweet_text.strip()

        if len(tweet_text) > 600:
            last_period = tweet_text[:597].rfind(".")
            if last_period > 200:
                tweet_text = tweet_text[:last_period + 1]
            else:
                tweet_text = tweet_text[:597] + "..."

        hashtags = self._pick_hashtags(content_type)
        if len(tweet_text) + len(hashtags) + 2 <= 600:
            tweet_text = tweet_text.rstrip() + "\n\n" + hashtags

        mt = MarketingTweet(
            content=tweet_text,
            content_type=content_type,
            ai_model_used=settings.anthropic_model,
            status="draft",
            hashtags=hashtags,
        )
        db.add(mt)
        await db.commit()
        await db.refresh(mt)
        logger.info("Generated GTM tweet #%s [%s]: %s", mt.id, content_type, tweet_text[:80])
        return mt

    async def _build_user_prompt(
        self, content_type: str, db: AsyncSession, custom_topic: Optional[str] = None
    ) -> str:
        if custom_topic:
            return f"Write a tweet about: {custom_topic}"

        if content_type == "product":
            topic = random.choice(PRODUCT_TOPICS)
            return f"Write a tweet about this kualia.ai feature: {topic}"

        elif content_type == "industry":
            topic = random.choice(INDUSTRY_TOPICS)
            return f"Write a tweet sharing your perspective on: {topic}"

        elif content_type == "educational":
            topic = random.choice(EDUCATIONAL_TOPICS)
            return f"Write an educational tweet explaining: {topic}"

        elif content_type == "showcase":
            showcase_data = await self._get_showcase_data(db)
            if showcase_data:
                return f"Write a tweet showcasing this result from kualia.ai:\n{showcase_data}"
            topic = random.choice(PRODUCT_TOPICS)
            return f"Write a showcase-style tweet about: {topic}"

        return "Write a compelling tweet about kualia.ai's RL environment generation platform."

    async def _get_showcase_data(self, db: AsyncSession) -> Optional[str]:
        """Pull real platform data for showcase tweets."""
        try:
            result = await db.execute(
                select(RLEnvironment)
                .where(RLEnvironment.status == "published")
                .order_by(func.random())
                .limit(1)
            )
            env = result.scalar_one_or_none()
            if env:
                runs_result = await db.execute(
                    select(TrainingRun)
                    .where(TrainingRun.env_id == env.id, TrainingRun.status == "completed")
                    .order_by(TrainingRun.completed_at.desc())
                    .limit(1)
                )
                run = runs_result.scalar_one_or_none()
                info = f"Environment: {env.name}\nDomain: {env.domain or env.category}\nDescription: {(env.description or '')[:200]}"
                if run and run.results_json:
                    try:
                        results = json.loads(run.results_json)
                        info += f"\nAlgorithm: {run.algorithm}"
                        info += f"\nMean Reward: {results.get('mean_reward', 'N/A')}"
                        info += f"\nSuccess Rate: {results.get('success_rate', 'N/A')}"
                    except (json.JSONDecodeError, TypeError):
                        pass
                return info
        except Exception as e:
            logger.warning("Showcase data fetch failed: %s", e)
        return None

    def _pick_hashtags(self, content_type: str, count: int = 3) -> str:
        base = ["#ReinforcementLearning", "#AI"]
        extras = {
            "product": ["#kualia", "#RLEnvironment", "#AgentTraining"],
            "industry": ["#MLResearch", "#DeepRL", "#MachineLearning"],
            "educational": ["#LearnRL", "#MachineLearning", "#DeepRL"],
            "showcase": ["#kualia", "#RLResults", "#AgentTraining"],
        }
        pool = base + extras.get(content_type, [])
        selected = random.sample(pool, min(count, len(pool)))
        return " ".join(selected)

    async def get_content_calendar(self, days: int = 7) -> List[Dict]:
        """Generate a content calendar suggestion for the next N days."""
        calendar = []
        schedule = [
            {"time": "09:00", "type": "educational"},
            {"time": "14:00", "type": "product"},
            {"time": "20:00", "type": "industry"},
        ]
        now = datetime.utcnow()
        for day_offset in range(days):
            date = now + timedelta(days=day_offset)
            for slot in schedule:
                calendar.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "time": slot["time"],
                    "content_type": slot["type"],
                    "status": "planned",
                })
        return calendar

    async def get_stats(self, db: AsyncSession) -> Dict:
        """Get marketing performance stats."""
        total = await db.execute(select(func.count(MarketingTweet.id)))
        posted = await db.execute(
            select(func.count(MarketingTweet.id)).where(MarketingTweet.status == "posted")
        )
        drafts = await db.execute(
            select(func.count(MarketingTweet.id)).where(MarketingTweet.status == "draft")
        )

        total_likes = await db.execute(select(func.sum(MarketingTweet.likes)))
        total_impressions = await db.execute(select(func.sum(MarketingTweet.impressions)))
        total_engagement = await db.execute(
            select(func.count(EngagementLog.id))
        )

        week_ago = datetime.utcnow() - timedelta(days=7)
        weekly_tweets = await db.execute(
            select(func.count(MarketingTweet.id)).where(
                MarketingTweet.status == "posted",
                MarketingTweet.posted_at >= week_ago,
            )
        )
        weekly_engagements = await db.execute(
            select(func.count(EngagementLog.id)).where(EngagementLog.created_at >= week_ago)
        )

        return {
            "total_tweets": total.scalar() or 0,
            "posted_tweets": posted.scalar() or 0,
            "draft_tweets": drafts.scalar() or 0,
            "total_likes": total_likes.scalar() or 0,
            "total_impressions": total_impressions.scalar() or 0,
            "total_engagements": total_engagement.scalar() or 0,
            "weekly_tweets": weekly_tweets.scalar() or 0,
            "weekly_engagements": weekly_engagements.scalar() or 0,
        }


    # -------------------------------------------------------
    # EVALUATION & STRATEGY ENGINE
    # -------------------------------------------------------

    EVAL_SYSTEM_PROMPT = """You are the GTM Strategy AI for kualia.ai, an RL environment generation platform.
You are given performance metrics from the last period. Analyze the data and provide:

1. ANALYSIS: What's working, what's not. Be specific with numbers.
2. SCORE: Overall GTM health from 0-100 (0=dead, 50=average, 80=good, 100=excellent)
3. RECOMMENDATIONS: 3-5 specific, actionable next steps

Consider:
- Tweet content types: which get more engagement?
- Prospect pipeline: are we finding the right people? conversion rates?
- Reply strategy: are value-add replies generating interest?
- Search queries: which find the best prospects?
- Community presence: are we becoming known in RL circles?
- Cost efficiency: are we getting results per API call?

Respond in JSON:
{
  "score": N,
  "analysis": "2-3 paragraph analysis",
  "recommendations": [
    {"priority": "high/medium/low", "action": "specific action", "reason": "why this matters"},
    ...
  ]
}"""

    async def run_evaluation(self, db: AsyncSession, days: int = 7, report_type: str = "manual") -> Dict:
        """Collect metrics, analyze with AI, produce an evaluation report."""
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=days)

        metrics = await self._collect_evaluation_metrics(db, period_start, period_end)

        metrics_text = json.dumps(metrics, indent=2, default=str)
        user_prompt = f"Period: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')} ({days} days)\n\nMetrics:\n{metrics_text}\n\nAnalyze and recommend."

        try:
            raw = await ai_service._call_ai(self.EVAL_SYSTEM_PROMPT, user_prompt, max_tokens=1500)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1].replace("json", "").strip()
            eval_data = json.loads(raw)
        except Exception as e:
            logger.error("GTM evaluation AI call failed: %s", e)
            eval_data = {
                "score": 0,
                "analysis": f"Evaluation failed: {str(e)}",
                "recommendations": [],
            }

        report = GTMReport(
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            metrics_json=metrics_text,
            analysis=eval_data.get("analysis", ""),
            recommendations=json.dumps(eval_data.get("recommendations", [])),
            score=eval_data.get("score", 0),
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)

        logger.info("GTM evaluation report #%s: score=%s", report.id, report.score)
        return {
            "id": report.id,
            "score": report.score,
            "analysis": report.analysis,
            "recommendations": eval_data.get("recommendations", []),
            "metrics": metrics,
            "period": f"{period_start.strftime('%Y-%m-%d')} - {period_end.strftime('%Y-%m-%d')}",
        }

    async def _collect_evaluation_metrics(self, db: AsyncSession, start: datetime, end: datetime) -> Dict:
        """Gather all relevant metrics for the evaluation period."""

        tweets_posted = (await db.execute(
            select(func.count(MarketingTweet.id)).where(
                MarketingTweet.status == "posted",
                MarketingTweet.posted_at >= start,
                MarketingTweet.posted_at <= end,
            )
        )).scalar() or 0

        tweets_by_type = {}
        for ct in CONTENT_TYPES:
            count = (await db.execute(
                select(func.count(MarketingTweet.id)).where(
                    MarketingTweet.status == "posted",
                    MarketingTweet.content_type == ct,
                    MarketingTweet.posted_at >= start,
                    MarketingTweet.posted_at <= end,
                )
            )).scalar() or 0
            total_likes = (await db.execute(
                select(func.sum(MarketingTweet.likes)).where(
                    MarketingTweet.content_type == ct,
                    MarketingTweet.posted_at >= start,
                    MarketingTweet.posted_at <= end,
                )
            )).scalar() or 0
            total_impressions = (await db.execute(
                select(func.sum(MarketingTweet.impressions)).where(
                    MarketingTweet.content_type == ct,
                    MarketingTweet.posted_at >= start,
                    MarketingTweet.posted_at <= end,
                )
            )).scalar() or 0
            tweets_by_type[ct] = {
                "count": count,
                "total_likes": total_likes,
                "total_impressions": total_impressions,
                "avg_likes": round(total_likes / max(count, 1), 1),
            }

        likes_given = (await db.execute(
            select(func.count(EngagementLog.id)).where(
                EngagementLog.action_type == "like",
                EngagementLog.status == "completed",
                EngagementLog.created_at >= start,
                EngagementLog.created_at <= end,
            )
        )).scalar() or 0

        replies_sent = (await db.execute(
            select(func.count(EngagementLog.id)).where(
                EngagementLog.action_type == "reply",
                EngagementLog.created_at >= start,
                EngagementLog.created_at <= end,
            )
        )).scalar() or 0

        reply_suggestions = (await db.execute(
            select(func.count(EngagementLog.id)).where(
                EngagementLog.action_type == "reply_suggestion",
                EngagementLog.created_at >= start,
                EngagementLog.created_at <= end,
            )
        )).scalar() or 0

        prospects_new = (await db.execute(
            select(func.count(Prospect.id)).where(
                Prospect.created_at >= start,
                Prospect.created_at <= end,
            )
        )).scalar() or 0

        prospects_by_stage = {}
        for stage in ["detected", "engaged", "warm", "converted", "disqualified"]:
            prospects_by_stage[stage] = (await db.execute(
                select(func.count(Prospect.id)).where(Prospect.stage == stage)
            )).scalar() or 0

        avg_prospect_score = (await db.execute(
            select(func.avg(Prospect.score))
        )).scalar() or 0

        top_queries = await db.execute(
            select(
                EngagementLog.search_query,
                func.count(EngagementLog.id).label("uses"),
            )
            .where(
                EngagementLog.created_at >= start,
                EngagementLog.created_at <= end,
                EngagementLog.search_query.isnot(None),
            )
            .group_by(EngagementLog.search_query)
            .order_by(func.count(EngagementLog.id).desc())
            .limit(5)
        )
        top_queries_list = [{"query": r[0], "uses": r[1]} for r in top_queries.fetchall()]

        return {
            "period_days": (end - start).days,
            "tweets": {
                "total_posted": tweets_posted,
                "by_type": tweets_by_type,
            },
            "engagement": {
                "likes_given": likes_given,
                "replies_sent": replies_sent,
                "reply_suggestions_generated": reply_suggestions,
                "reply_approval_rate": round(replies_sent / max(reply_suggestions, 1) * 100, 1),
            },
            "prospects": {
                "new_this_period": prospects_new,
                "by_stage": prospects_by_stage,
                "avg_score": round(avg_prospect_score, 1),
            },
            "top_search_queries": top_queries_list,
        }

    async def get_reports(self, db: AsyncSession, limit: int = 10) -> List[Dict]:
        """Get recent GTM evaluation reports."""
        result = await db.execute(
            select(GTMReport)
            .order_by(GTMReport.created_at.desc())
            .limit(limit)
        )
        reports = result.scalars().all()
        out = []
        for r in reports:
            recs = []
            if r.recommendations:
                try:
                    recs = json.loads(r.recommendations)
                except (json.JSONDecodeError, TypeError):
                    pass
            out.append({
                "id": r.id,
                "report_type": r.report_type,
                "period": f"{r.period_start.strftime('%Y-%m-%d')} - {r.period_end.strftime('%Y-%m-%d')}",
                "score": r.score,
                "analysis": r.analysis,
                "recommendations": recs,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })
        return out


gtm_service = GTMService()
