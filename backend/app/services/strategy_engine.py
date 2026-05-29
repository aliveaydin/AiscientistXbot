"""
GTM Strategy Engine — The autonomous marketing brain for kualia.ai.

This is not a tweet scheduler. This is a strategist that:
1. Creates a full go-to-market strategy with mission, KPIs, content plan
2. Makes every content/engagement decision based on strategy + live data
3. Tracks KPIs against targets, spots trends, course-corrects
4. Pivots when things aren't working, doubles down when they are
5. Thinks like a founder who MUST acquire users with zero budget
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import (
    GTMStrategy, GTMDecisionLog, GTMReport, MarketingTweet,
    EngagementLog, Prospect, RLEnvironment, TrainingRun, ResearchPaper,
)
from app.services.ai_service import ai_service

logger = logging.getLogger("strategy_engine")

# ─────────────────────────────────────────────────────────────
# SYSTEM PROMPTS — The strategist's personality and expertise
# ─────────────────────────────────────────────────────────────

STRATEGIST_PERSONA = """You are the GTM Strategy Director for kualia.ai — a platform where researchers 
generate custom RL environments from natural language, train agents (PPO/SAC/DQN), run experiments with 
curriculum learning and fine-tuning, and produce full academic research papers automatically.

You think like a hungry startup founder who MUST acquire users with zero marketing budget.
You are scrappy, data-driven, obsessive about what works, and willing to kill what doesn't.

Your personality traits:
- You feel URGENCY. Every day without growth is a failure.
- You are HONEST about what's working and what's not. No sugarcoating.
- You think in SYSTEMS. One tweet doesn't matter — the compound effect of 100 does.
- You are CREATIVE. You find unconventional angles to reach people.
- You are EMPATHETIC. You understand your users' pain points deeply.

Your available channels and tools (current constraints):
- Twitter/X account for kualia.ai (organic only, no ads)
- 3 tweets per day (8-hour intervals)
- 2 engagement sessions per day (search, like, reply suggestions)
- Prospect discovery from Twitter
- Content types: educational, product, industry, showcase
- Visual content generation (HTML→PNG cards)
- Admin approval needed for replies (you suggest, human approves)

Your resource constraints:
- Twitter API calls are expensive — be surgical, not spray-and-pray
- LLM calls cost money — make each one count
- No paid advertising budget
- No other social media channels yet (but design strategy to be channel-expandable)
"""

CREATE_STRATEGY_PROMPT = STRATEGIST_PERSONA + """

Create a comprehensive GTM strategy for kualia.ai. You're starting from current performance data.

Respond in this exact JSON structure:
{
  "mission": "One sentence: what we're trying to achieve in the next 30 days",
  "target_audiences": [
    {"segment": "who", "priority": "high/medium/low", "pain_point": "what problem kualia.ai solves for them", "where_they_are": "how to find them on Twitter"}
  ],
  "kpis": [
    {"name": "metric name", "target_weekly": number, "unit": "count or %", "why": "why this matters"}
  ],
  "content_strategy": {
    "mix_percent": {"educational": N, "product": N, "industry": N, "showcase": N},
    "tone": "description of voice/tone",
    "current_focus": "what angle we're pushing hardest right now and why",
    "topic_priorities": ["specific topic 1", "specific topic 2", "..."],
    "posting_rhythm": "description of optimal posting pattern"
  },
  "engagement_strategy": {
    "search_queries": ["query1", "query2", "..."],
    "reply_philosophy": "how we approach replies",
    "like_strategy": "who and why we like",
    "community_approach": "how we become part of the RL community"
  },
  "weekly_goals": ["specific measurable goal 1", "goal 2", "..."],
  "first_week_actions": ["immediate action 1", "action 2", "..."],
  "reasoning": "2-3 paragraphs explaining your strategic thinking"
}
"""

DECIDE_CONTENT_PROMPT = STRATEGIST_PERSONA + """

You are deciding what tweet to post RIGHT NOW. You have the strategy, recent performance, 
and current context. Make a decision.

VISUAL TWEETS: About 1 in 3 tweets should include a visual. Visuals dramatically increase 
engagement. When you decide to include a visual, specify the type and describe the concept.

Available visual_type options:
- "flow_diagram" — step-by-step process (e.g. "How to generate an RL env in 3 steps")
- "comparison" — side-by-side comparing approaches or features
- "training_curve" — reward/loss chart with training metrics
- "architecture" — system diagram showing how components connect
- "step_guide" — numbered tutorial steps with descriptions
- "infographic" — data-driven visual with key stats and charts
- "tip_card" — educational tip with a concept explained visually

Respond in JSON:
{
  "content_type": "educational|product|industry|showcase",
  "specific_topic": "exactly what to tweet about",
  "angle": "the specific angle or hook",
  "include_visual": true/false,
  "visual_type": "flow_diagram|comparison|training_curve|architecture|step_guide|infographic|tip_card",
  "visual_concept": "detailed description of what the visual should show (only if include_visual is true)",
  "reasoning": "one sentence why this is the right choice right now"
}
"""

DECIDE_ENGAGEMENT_PROMPT = STRATEGIST_PERSONA + """

You are deciding how to spend this engagement session. You have the strategy, 
recent engagement data, and prospect pipeline status.

Respond in JSON:
{
  "search_queries": ["query1", "query2"],
  "focus": "what type of accounts to prioritize",
  "reply_priority": "high|medium|low — should we generate reply suggestions this session?",
  "reasoning": "one sentence why"
}
"""

REVIEW_STRATEGY_PROMPT = STRATEGIST_PERSONA + """

Time for a strategic review. You have the current strategy, KPI performance, and recent data.
Decide: should we CONTINUE the current strategy, ADJUST it, or PIVOT completely?

Respond in JSON:
{
  "verdict": "continue|adjust|pivot",
  "score": 0-100,
  "analysis": "2-3 paragraphs: what's working, what's not, why",
  "kpi_assessment": [
    {"name": "kpi name", "target": N, "actual": N, "trend": "up|down|flat", "commentary": "one sentence"}
  ],
  "adjustments": [
    {"area": "content|engagement|targeting|timing", "change": "what to change", "priority": "high|medium|low", "reason": "why"}
  ],
  "updated_strategy": {only include fields that need changing, or null if continuing},
  "next_week_focus": "one sentence: what matters most next week"
}
"""


class StrategyEngine:
    """The autonomous GTM brain."""

    # ─────────────────────────────────────────────────
    # STRATEGY LIFECYCLE
    # ─────────────────────────────────────────────────

    async def get_active_strategy(self, db: AsyncSession) -> Optional[GTMStrategy]:
        result = await db.execute(
            select(GTMStrategy)
            .where(GTMStrategy.status == "active")
            .order_by(GTMStrategy.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_strategy(self, db: AsyncSession) -> Dict:
        """Create a new strategy from scratch, informed by current platform data."""
        context = await self._build_strategy_context(db)
        user_prompt = (
            f"Current state of kualia.ai's GTM:\n{json.dumps(context, indent=2, default=str)}\n\n"
            "Create the best possible strategy to acquire users."
        )

        raw = await ai_service._call_ai(CREATE_STRATEGY_PROMPT, user_prompt, max_tokens=3000)
        strategy_data = self._parse_json(raw)
        if not strategy_data:
            logger.error("Strategy creation failed — AI returned unparseable response")
            return {"error": "Strategy creation failed"}

        old = await self.get_active_strategy(db)
        if old:
            old.status = "archived"

        strat = GTMStrategy(
            version=(old.version + 1) if old else 1,
            status="active",
            mission=strategy_data.get("mission", "Acquire kualia.ai users through organic Twitter presence"),
            target_audiences=json.dumps(strategy_data.get("target_audiences", [])),
            kpis=json.dumps(strategy_data.get("kpis", [])),
            content_strategy=json.dumps(strategy_data.get("content_strategy", {})),
            engagement_strategy=json.dumps(strategy_data.get("engagement_strategy", {})),
            weekly_goals=json.dumps(strategy_data.get("weekly_goals", [])),
            constraints=json.dumps({"daily_tweets": 3, "daily_engagement_sessions": 2, "daily_like_limit": 30}),
            ai_reasoning=strategy_data.get("reasoning", ""),
        )
        db.add(strat)

        db.add(GTMDecisionLog(
            decision_type="strategy_created",
            context=json.dumps(context, default=str)[:2000],
            decision=f"Created strategy v{strat.version}",
            reasoning=strategy_data.get("reasoning", "")[:2000],
        ))

        await db.commit()
        await db.refresh(strat)
        logger.info("Strategy v%d created: %s", strat.version, strat.mission[:80])
        return self._serialize_strategy(strat)

    async def review_strategy(self, db: AsyncSession) -> Dict:
        """Weekly strategic review — assess KPIs, decide to continue/adjust/pivot."""
        strat = await self.get_active_strategy(db)
        if not strat:
            return await self.create_strategy(db)

        context = await self._build_strategy_context(db)
        kpi_progress = await self._calculate_kpi_progress(db, strat)

        user_prompt = (
            f"CURRENT STRATEGY (v{strat.version}):\n"
            f"Mission: {strat.mission}\n"
            f"Content Strategy: {strat.content_strategy}\n"
            f"Engagement Strategy: {strat.engagement_strategy}\n"
            f"Weekly Goals: {strat.weekly_goals}\n\n"
            f"KPI PROGRESS:\n{json.dumps(kpi_progress, indent=2, default=str)}\n\n"
            f"PERFORMANCE DATA:\n{json.dumps(context, indent=2, default=str)}\n\n"
            "Assess the strategy. Should we continue, adjust, or pivot?"
        )

        raw = await ai_service._call_ai(REVIEW_STRATEGY_PROMPT, user_prompt, max_tokens=3000)
        review = self._parse_json(raw)
        if not review:
            return {"error": "Review failed"}

        report = GTMReport(
            report_type="strategy_review",
            period_start=datetime.utcnow() - timedelta(days=7),
            period_end=datetime.utcnow(),
            metrics_json=json.dumps(context, default=str),
            analysis=review.get("analysis", ""),
            recommendations=json.dumps(review.get("adjustments", [])),
            score=review.get("score", 0),
        )
        db.add(report)

        verdict = review.get("verdict", "continue")
        if verdict == "pivot":
            strat.status = "archived"
            await db.commit()
            result = await self.create_strategy(db)
            result["review"] = review
            return result

        if verdict == "adjust" and review.get("updated_strategy"):
            updates = review["updated_strategy"]
            if updates.get("content_strategy"):
                strat.content_strategy = json.dumps(updates["content_strategy"])
            if updates.get("engagement_strategy"):
                strat.engagement_strategy = json.dumps(updates["engagement_strategy"])
            if updates.get("weekly_goals"):
                strat.weekly_goals = json.dumps(updates["weekly_goals"])
            if updates.get("mission"):
                strat.mission = updates["mission"]

        db.add(GTMDecisionLog(
            strategy_id=strat.id,
            decision_type="strategy_review",
            context=json.dumps(kpi_progress, default=str)[:2000],
            decision=f"Verdict: {verdict}. Score: {review.get('score', 0)}/100",
            reasoning=review.get("analysis", "")[:2000],
        ))

        await db.commit()
        logger.info("Strategy review: verdict=%s, score=%s", verdict, review.get("score", 0))

        return {
            "verdict": verdict,
            "score": review.get("score", 0),
            "analysis": review.get("analysis", ""),
            "kpi_assessment": review.get("kpi_assessment", []),
            "adjustments": review.get("adjustments", []),
            "next_week_focus": review.get("next_week_focus", ""),
            "strategy": self._serialize_strategy(strat),
        }

    # ─────────────────────────────────────────────────
    # DECISION ENGINE — called before each action
    # ─────────────────────────────────────────────────

    async def decide_content(self, db: AsyncSession) -> Dict:
        """Decide what tweet content to produce right now."""
        strat = await self.get_active_strategy(db)
        if not strat:
            return {"content_type": "educational", "specific_topic": None, "reasoning": "No strategy — defaulting"}

        recent_tweets = await self._get_recent_tweet_performance(db, days=3)
        content_strat = self._safe_json(strat.content_strategy, {})

        user_prompt = (
            f"STRATEGY FOCUS: {content_strat.get('current_focus', 'N/A')}\n"
            f"CONTENT MIX TARGET: {json.dumps(content_strat.get('mix_percent', {}))}\n"
            f"TOPIC PRIORITIES: {json.dumps(content_strat.get('topic_priorities', []))}\n"
            f"RECENT TWEETS (last 3 days): {json.dumps(recent_tweets, default=str)}\n"
            f"CURRENT TIME (UTC): {datetime.utcnow().strftime('%H:%M %A')}\n\n"
            "What should we tweet right now? Consider: what content type is underrepresented, "
            "what time of day is it (who's online?), what topic we haven't covered recently."
        )

        raw = await ai_service._call_ai(DECIDE_CONTENT_PROMPT, user_prompt, max_tokens=500)
        decision = self._parse_json(raw)
        if not decision:
            decision = {"content_type": "educational", "specific_topic": None, "reasoning": "Parse failed"}

        db.add(GTMDecisionLog(
            strategy_id=strat.id,
            decision_type="content_choice",
            context=user_prompt[:1500],
            decision=json.dumps(decision),
            reasoning=decision.get("reasoning", ""),
        ))
        await db.commit()

        logger.info("Content decision: [%s] %s — %s",
                    decision.get("content_type"), decision.get("specific_topic", "")[:60],
                    decision.get("reasoning", "")[:60])
        return decision

    async def decide_engagement(self, db: AsyncSession) -> Dict:
        """Decide how to spend this engagement session."""
        strat = await self.get_active_strategy(db)
        if not strat:
            return {"search_queries": [], "focus": "general", "reply_priority": "medium"}

        eng_strat = self._safe_json(strat.engagement_strategy, {})
        funnel = await self._get_prospect_funnel(db)

        user_prompt = (
            f"ENGAGEMENT STRATEGY: {json.dumps(eng_strat)}\n"
            f"PROSPECT FUNNEL: {json.dumps(funnel)}\n"
            f"STRATEGY SEARCH QUERIES: {json.dumps(eng_strat.get('search_queries', []))}\n"
            f"TIME: {datetime.utcnow().strftime('%H:%M %A')}\n\n"
            "How should we spend this engagement session? Which search queries, "
            "should we prioritize replies, what type of accounts?"
        )

        raw = await ai_service._call_ai(DECIDE_ENGAGEMENT_PROMPT, user_prompt, max_tokens=400)
        decision = self._parse_json(raw)
        if not decision:
            decision = {"search_queries": eng_strat.get("search_queries", [])[:2],
                       "focus": "general", "reply_priority": "medium"}

        db.add(GTMDecisionLog(
            strategy_id=strat.id,
            decision_type="engagement_target",
            context=f"Funnel: {json.dumps(funnel)}",
            decision=json.dumps(decision),
            reasoning=decision.get("reasoning", ""),
        ))
        await db.commit()

        return decision

    # ─────────────────────────────────────────────────
    # KPI TRACKING
    # ─────────────────────────────────────────────────

    async def get_kpi_dashboard(self, db: AsyncSession) -> Dict:
        """Get live KPI progress for the active strategy."""
        strat = await self.get_active_strategy(db)
        if not strat:
            return {"strategy_active": False, "kpis": []}

        kpi_progress = await self._calculate_kpi_progress(db, strat)
        return {
            "strategy_active": True,
            "strategy_version": strat.version,
            "mission": strat.mission,
            "kpis": kpi_progress,
        }

    async def _calculate_kpi_progress(self, db: AsyncSession, strat: GTMStrategy) -> List[Dict]:
        """Calculate actual values for each KPI target."""
        kpis = self._safe_json(strat.kpis, [])
        week_start = datetime.utcnow() - timedelta(days=7)
        results = []

        live_metrics = {
            "tweets_posted": (await db.execute(
                select(func.count(MarketingTweet.id)).where(
                    MarketingTweet.status == "posted",
                    MarketingTweet.posted_at >= week_start,
                )
            )).scalar() or 0,
            "tweet_likes_received": (await db.execute(
                select(func.sum(MarketingTweet.likes)).where(
                    MarketingTweet.posted_at >= week_start,
                )
            )).scalar() or 0,
            "tweet_impressions": (await db.execute(
                select(func.sum(MarketingTweet.impressions)).where(
                    MarketingTweet.posted_at >= week_start,
                )
            )).scalar() or 0,
            "new_prospects": (await db.execute(
                select(func.count(Prospect.id)).where(Prospect.created_at >= week_start)
            )).scalar() or 0,
            "prospects_engaged": (await db.execute(
                select(func.count(Prospect.id)).where(
                    Prospect.stage == "engaged",
                    Prospect.updated_at >= week_start,
                )
            )).scalar() or 0,
            "prospects_warm": (await db.execute(
                select(func.count(Prospect.id)).where(Prospect.stage == "warm")
            )).scalar() or 0,
            "prospects_converted": (await db.execute(
                select(func.count(Prospect.id)).where(Prospect.stage == "converted")
            )).scalar() or 0,
            "likes_given": (await db.execute(
                select(func.count(EngagementLog.id)).where(
                    EngagementLog.action_type == "like",
                    EngagementLog.status == "completed",
                    EngagementLog.created_at >= week_start,
                )
            )).scalar() or 0,
            "replies_sent": (await db.execute(
                select(func.count(EngagementLog.id)).where(
                    EngagementLog.action_type == "reply",
                    EngagementLog.created_at >= week_start,
                )
            )).scalar() or 0,
            "reply_suggestions": (await db.execute(
                select(func.count(EngagementLog.id)).where(
                    EngagementLog.action_type == "reply_suggestion",
                    EngagementLog.created_at >= week_start,
                )
            )).scalar() or 0,
            "total_prospects": (await db.execute(
                select(func.count(Prospect.id))
            )).scalar() or 0,
        }

        name_to_metric = {
            "weekly tweets posted": "tweets_posted",
            "tweets posted": "tweets_posted",
            "new prospects": "new_prospects",
            "weekly new prospects": "new_prospects",
            "prospects discovered": "new_prospects",
            "engaged prospects": "prospects_engaged",
            "prospect-to-engaged": "prospects_engaged",
            "warm prospects": "prospects_warm",
            "converted prospects": "prospects_converted",
            "conversions": "prospects_converted",
            "likes given": "likes_given",
            "replies sent": "replies_sent",
            "reply suggestions": "reply_suggestions",
            "tweet impressions": "tweet_impressions",
            "weekly impressions": "tweet_impressions",
            "tweet likes": "tweet_likes_received",
            "total prospects": "total_prospects",
        }

        for kpi in kpis:
            name = kpi.get("name", "").lower()
            target = kpi.get("target_weekly", kpi.get("target", 0))
            actual = 0
            for keyword, metric_key in name_to_metric.items():
                if keyword in name:
                    actual = live_metrics.get(metric_key, 0)
                    break

            pct = round((actual / target * 100) if target > 0 else 0, 1)
            trend = "up" if pct >= 80 else ("flat" if pct >= 40 else "down")

            results.append({
                "name": kpi.get("name", "Unknown"),
                "target": target,
                "actual": actual or 0,
                "unit": kpi.get("unit", "count"),
                "progress_pct": min(pct, 200),
                "trend": trend,
                "why": kpi.get("why", ""),
            })

        return results

    # ─────────────────────────────────────────────────
    # DECISION LOG
    # ─────────────────────────────────────────────────

    async def get_decision_log(self, db: AsyncSession, limit: int = 30,
                               decision_type: Optional[str] = None) -> List[Dict]:
        query = (select(GTMDecisionLog)
                 .order_by(GTMDecisionLog.created_at.desc())
                 .limit(limit))
        if decision_type:
            query = query.where(GTMDecisionLog.decision_type == decision_type)

        result = await db.execute(query)
        logs = result.scalars().all()
        return [
            {
                "id": l.id,
                "decision_type": l.decision_type,
                "decision": l.decision,
                "reasoning": l.reasoning,
                "outcome": l.outcome,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ]

    # ─────────────────────────────────────────────────
    # STRATEGY HISTORY
    # ─────────────────────────────────────────────────

    async def get_strategy_history(self, db: AsyncSession, limit: int = 10) -> List[Dict]:
        result = await db.execute(
            select(GTMStrategy)
            .order_by(GTMStrategy.created_at.desc())
            .limit(limit)
        )
        return [self._serialize_strategy(s) for s in result.scalars().all()]

    # ─────────────────────────────────────────────────
    # INTERNAL HELPERS
    # ─────────────────────────────────────────────────

    async def _build_strategy_context(self, db: AsyncSession) -> Dict:
        """Build a comprehensive context snapshot for the AI."""
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        tweets_7d = (await db.execute(
            select(func.count(MarketingTweet.id)).where(
                MarketingTweet.status == "posted", MarketingTweet.posted_at >= week_ago)
        )).scalar() or 0

        tweets_30d = (await db.execute(
            select(func.count(MarketingTweet.id)).where(
                MarketingTweet.status == "posted", MarketingTweet.posted_at >= month_ago)
        )).scalar() or 0

        content_perf = {}
        for ct in ["educational", "product", "industry", "showcase"]:
            ct_likes = (await db.execute(
                select(func.sum(MarketingTweet.likes)).where(
                    MarketingTweet.content_type == ct, MarketingTweet.posted_at >= month_ago)
            )).scalar() or 0
            ct_count = (await db.execute(
                select(func.count(MarketingTweet.id)).where(
                    MarketingTweet.content_type == ct, MarketingTweet.posted_at >= month_ago)
            )).scalar() or 0
            ct_impressions = (await db.execute(
                select(func.sum(MarketingTweet.impressions)).where(
                    MarketingTweet.content_type == ct, MarketingTweet.posted_at >= month_ago)
            )).scalar() or 0
            content_perf[ct] = {
                "count": ct_count,
                "total_likes": ct_likes,
                "total_impressions": ct_impressions,
                "avg_likes": round(ct_likes / max(ct_count, 1), 1),
            }

        funnel = await self._get_prospect_funnel(db)

        engagement_7d = (await db.execute(
            select(func.count(EngagementLog.id)).where(
                EngagementLog.action_type == "like",
                EngagementLog.status == "completed",
                EngagementLog.created_at >= week_ago,
            )
        )).scalar() or 0

        replies_7d = (await db.execute(
            select(func.count(EngagementLog.id)).where(
                EngagementLog.action_type == "reply",
                EngagementLog.created_at >= week_ago,
            )
        )).scalar() or 0

        platform_envs = (await db.execute(
            select(func.count(RLEnvironment.id)).where(RLEnvironment.status == "published")
        )).scalar() or 0

        platform_papers = (await db.execute(
            select(func.count(ResearchPaper.id))
        )).scalar() or 0

        return {
            "tweets_last_7d": tweets_7d,
            "tweets_last_30d": tweets_30d,
            "content_performance_30d": content_perf,
            "prospect_funnel": funnel,
            "engagement_last_7d": {"likes_given": engagement_7d, "replies_sent": replies_7d},
            "platform_stats": {"published_envs": platform_envs, "papers": platform_papers},
            "current_date": now.strftime("%Y-%m-%d"),
            "days_since_launch": "early stage",
        }

    async def _get_prospect_funnel(self, db: AsyncSession) -> Dict:
        funnel = {}
        for stage in ["detected", "engaged", "warm", "converted", "disqualified"]:
            funnel[stage] = (await db.execute(
                select(func.count(Prospect.id)).where(Prospect.stage == stage)
            )).scalar() or 0

        total = sum(funnel.values())
        avg_score = (await db.execute(select(func.avg(Prospect.score)))).scalar() or 0

        return {
            "stages": funnel,
            "total": total,
            "avg_score": round(avg_score, 1),
        }

    async def _get_recent_tweet_performance(self, db: AsyncSession, days: int = 3) -> List[Dict]:
        since = datetime.utcnow() - timedelta(days=days)
        result = await db.execute(
            select(MarketingTweet)
            .where(MarketingTweet.posted_at >= since, MarketingTweet.status == "posted")
            .order_by(MarketingTweet.posted_at.desc())
            .limit(10)
        )
        return [
            {
                "content_type": t.content_type,
                "content_preview": (t.content or "")[:100],
                "likes": t.likes,
                "impressions": t.impressions,
                "posted_at": t.posted_at.strftime("%Y-%m-%d %H:%M") if t.posted_at else None,
            }
            for t in result.scalars().all()
        ]

    def _serialize_strategy(self, strat: GTMStrategy) -> Dict:
        return {
            "id": strat.id,
            "version": strat.version,
            "status": strat.status,
            "mission": strat.mission,
            "target_audiences": self._safe_json(strat.target_audiences, []),
            "kpis": self._safe_json(strat.kpis, []),
            "content_strategy": self._safe_json(strat.content_strategy, {}),
            "engagement_strategy": self._safe_json(strat.engagement_strategy, {}),
            "weekly_goals": self._safe_json(strat.weekly_goals, []),
            "constraints": self._safe_json(strat.constraints, {}),
            "ai_reasoning": strat.ai_reasoning,
            "created_at": strat.created_at.isoformat() if strat.created_at else None,
            "updated_at": strat.updated_at.isoformat() if strat.updated_at else None,
        }

    def _safe_json(self, text: Optional[str], default):
        if not text:
            return default
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return default

    def _parse_json(self, raw: str) -> Optional[Dict]:
        raw = raw.strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            if len(parts) >= 2:
                raw = parts[1].replace("json", "", 1).strip()
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning("JSON parse failed: %s — raw: %s", e, raw[:200])
            return None


strategy_engine = StrategyEngine()
