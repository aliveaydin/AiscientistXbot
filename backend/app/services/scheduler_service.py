import asyncio
import logging
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from app.models import Tweet, Reply, Article, ActivityLog, BotSettings, BlogPost
from app.services.ai_service import ai_service
from app.services.twitter_service import twitter_service, kualia_twitter_service
from app.services.article_service import ArticleService
from app.services.arxiv_service import arxiv_service
from app.services.gtm_service import gtm_service
from app.services.engagement_service import engagement_service
from app.services.visual_engine import visual_engine
from app.services.strategy_engine import strategy_engine
from app.config import settings

logger = logging.getLogger("scheduler")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")


class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self._tweet_interval = settings.tweet_interval_minutes
        self._auto_reply = settings.auto_reply_enabled

    async def _get_setting(self, key: str, default: str) -> str:
        async with async_session() as db:
            result = await db.execute(
                select(BotSettings).where(BotSettings.key == key)
            )
            setting = result.scalar_one_or_none()
            return setting.value if setting else default

    async def _get_ai_model(self) -> str:
        return await self._get_setting("default_ai_model", settings.default_ai_model)

    async def _should_post_thread(self, db: AsyncSession) -> bool:
        """Alternate: if the last posted tweet was normal, next should be a thread and vice versa."""
        result = await db.execute(
            select(Tweet.is_thread)
            .where(Tweet.status == "posted", Tweet.language == "en", Tweet.thread_order.is_(None) | (Tweet.thread_order == 0))
            .order_by(Tweet.posted_at.desc())
            .limit(1)
        )
        row = result.first()
        if row is None:
            return False
        last_was_thread = row[0] if row[0] else False
        return not last_was_thread

    async def _post_single_tweet(self, article, model, previous_tweets, db):
        """Generate and post a single EN tweet."""
        tweet_content = await ai_service.generate_tweet(
            article, model=model, previous_tweets=previous_tweets
        )
        if len(tweet_content) > 800:
            tweet_content = tweet_content[:797] + "..."

        tweet = Tweet(
            content=tweet_content, article_id=article.id, ai_model_used=model,
            status="queued", language="en",
        )
        db.add(tweet)
        await db.commit()
        await db.refresh(tweet)

        logger.info(f"Generated tweet ({len(tweet_content)} chars): {tweet_content[:80]}...")

        post_result = await twitter_service.post_tweet(tweet_content, db, tweet.id)
        if post_result["success"]:
            logger.info(f"Tweet posted: {post_result.get('tweet_id', '?')}")
            db.add(ActivityLog(action="auto_tweet_posted", details=f"Posted: {tweet_content[:100]}...", status="success"))
        else:
            logger.warning(f"Tweet failed: {post_result.get('error', '')[:100]}")
            db.add(ActivityLog(action="tweet_retry_pending", details=f"Queued: {post_result.get('error', '')[:150]}", status="warning"))
            await db.refresh(tweet)
            if tweet.status == "failed":
                tweet.status = "queued"
        await db.commit()

        return tweet, tweet_content

    async def _post_thread(self, article, model, previous_tweets, db):
        """Generate and post a 2-3 tweet thread as a reply chain."""
        thread_parts = await ai_service.generate_thread(
            article, model=model, previous_tweets=previous_tweets
        )
        logger.info(f"Generated thread with {len(thread_parts)} parts")

        thread_tweets = []
        last_twitter_id = None

        for i, part in enumerate(thread_parts):
            tweet = Tweet(
                content=part, article_id=article.id, ai_model_used=model,
                status="queued", language="en", is_thread=True, thread_order=i,
            )
            db.add(tweet)
            await db.commit()
            await db.refresh(tweet)

            if last_twitter_id is None:
                post_result = await twitter_service.post_tweet(part, db, tweet.id)
            else:
                loop = asyncio.get_event_loop()
                api_result = await loop.run_in_executor(
                    None, lambda tid=last_twitter_id: twitter_service._post_tweet_api(part, reply_to_id=tid)
                )
                if api_result["success"]:
                    tweet.tweet_id = api_result["tweet_id"]
                    tweet.status = "posted"
                    tweet.posted_at = datetime.utcnow()
                    await db.commit()
                    post_result = api_result
                else:
                    tweet.status = "failed"
                    await db.commit()
                    post_result = api_result

            if post_result.get("success"):
                last_twitter_id = post_result.get("tweet_id") or tweet.tweet_id
                logger.info(f"Thread {i+1}/{len(thread_parts)} posted: {part[:60]}...")
            else:
                logger.warning(f"Thread {i+1}/{len(thread_parts)} failed: {post_result.get('error', '')[:100]}")
                break

            thread_tweets.append(tweet)

        # Set thread_id on all tweets to the first tweet's DB id
        if thread_tweets:
            first_id = thread_tweets[0].id
            for t in thread_tweets:
                t.thread_id = first_id
            await db.commit()
            db.add(ActivityLog(
                action="thread_posted",
                details=f"Thread: {len(thread_tweets)} tweets posted for: {article.title[:60]}",
                status="success",
            ))
            await db.commit()

        first_tweet = thread_tweets[0] if thread_tweets else None
        first_content = thread_parts[0] if thread_parts else ""
        return first_tweet, first_content

    async def generate_and_post_tweet(self):
        """Main job: Pick an article, decide normal vs thread, generate and post EN + TR."""
        logger.info("=== TWEET JOB STARTED ===")
        async with async_session() as db:
            try:
                await ArticleService.scan_and_import_articles(db)

                article = await ArticleService.get_least_tweeted_article(db)
                if not article:
                    logger.warning("No articles available for tweet generation")
                    db.add(ActivityLog(action="tweet_skipped", details="No articles available", status="warning"))
                    await db.commit()
                    return

                logger.info(f"Selected article: #{article.id} - {article.title[:60]}")

                prev_result = await db.execute(
                    select(Tweet.content).where(Tweet.article_id == article.id)
                )
                previous_tweets = [row[0] for row in prev_result.fetchall()]
                model = await self._get_ai_model()

                tweet, tweet_content = await self._post_single_tweet(article, model, previous_tweets, db)

                # Post Turkish translation of the same tweet
                if tweet and tweet_content:
                    try:
                        tr_content = await ai_service.translate_tweet_to_turkish(tweet_content)
                        if tr_content and len(tr_content) > 20:
                            if len(tr_content) > 800:
                                tr_content = tr_content[:797] + "..."
                            tr_tweet = Tweet(
                                content=tr_content, article_id=article.id, ai_model_used=model,
                                status="queued", language="tr",
                            )
                            db.add(tr_tweet)
                            await db.commit()
                            await db.refresh(tr_tweet)
                            tr_result = await twitter_service.post_tweet(tr_content, db, tr_tweet.id)
                            if tr_result["success"]:
                                logger.info(f"Turkish tweet posted: {tr_content[:60]}...")
                            else:
                                logger.warning(f"Turkish tweet failed: {tr_result.get('error', '')[:100]}")
                    except Exception as tr_err:
                        logger.warning(f"Turkish tweet generation/posting failed: {tr_err}")

                # Generate blog articles
                if tweet:
                    try:
                        logger.info("Generating blog articles...")
                        auto_pub = (await self._get_setting("auto_publish_blog", "true")).lower() == "true"
                        pub_status = "published" if auto_pub else "draft"

                        en_blog = await ai_service.generate_blog_post(article, tweet_content, language="en", model=model)
                        blog_en = BlogPost(
                            tweet_id=tweet.id, article_id=article.id,
                            title=en_blog["title"], content=en_blog["content"],
                            language="en", ai_model_used=en_blog.get("model", model), status=pub_status,
                            published=auto_pub,
                            published_at=datetime.utcnow() if auto_pub else None,
                        )
                        db.add(blog_en)
                        await db.commit()
                        logger.info(f"Blog article generated: '{en_blog['title'][:60]}'")
                        db.add(ActivityLog(action="blog_generated", details=f"Blog: {en_blog['title'][:80]}", status="success"))
                        await db.commit()
                    except Exception as blog_err:
                        logger.error(f"Blog generation error: {blog_err}")
                        db.add(ActivityLog(action="blog_error", details=f"Blog failed: {str(blog_err)[:200]}", status="error"))
                        await db.commit()

                logger.info("=== TWEET JOB FINISHED ===")

            except Exception as e:
                logger.error(f"TWEET JOB ERROR: {e}", exc_info=True)
                db.add(ActivityLog(action="auto_tweet_error", details=f"Error: {str(e)}", status="error"))
                await db.commit()

    async def retry_queued_tweets(self):
        """Retry posting queued tweets that failed due to 503 or other transient errors."""
        logger.info("--- RETRY JOB running ---")
        async with async_session() as db:
            try:
                result = await db.execute(
                    select(Tweet)
                    .where(Tweet.status == "queued")
                    .order_by(Tweet.created_at.asc())
                    .limit(5)
                )
                queued_tweets = result.scalars().all()

                if not queued_tweets:
                    logger.info("No queued tweets to retry")
                    return

                logger.info(f"Retrying {len(queued_tweets)} queued tweets")

                for tweet in queued_tweets:
                    # Check retry count (stored in a simple way)
                    retry_count = tweet.retry_count if hasattr(tweet, 'retry_count') and tweet.retry_count else 0

                    if retry_count >= 50:
                        tweet.status = "failed"
                        log = ActivityLog(
                            action="tweet_retry_exhausted",
                            details=f"Tweet #{tweet.id} failed after {retry_count} retries",
                            status="error",
                        )
                        db.add(log)
                        continue

                    post_result = await twitter_service.post_tweet(tweet.content, db, tweet.id)

                    if post_result["success"]:
                        log = ActivityLog(
                            action="tweet_retry_success",
                            details=f"Tweet #{tweet.id} posted on retry: {tweet.content[:80]}...",
                            status="success",
                        )
                        db.add(log)
                    else:
                        # Keep as queued, increment retry
                        await db.refresh(tweet)
                        if tweet.status == "failed":
                            tweet.status = "queued"

                await db.commit()

            except Exception as e:
                logger.error(f"RETRY JOB ERROR: {e}", exc_info=True)
                log = ActivityLog(
                    action="retry_job_error",
                    details=f"Error in retry job: {str(e)}",
                    status="error",
                )
                db.add(log)
                await db.commit()

    async def _find_conversation_context(self, mention: dict, db) -> dict:
        """
        Find the conversation context for a mention.
        Traces the reply chain back to find:
        - The root tweet (our original tweet)
        - The article content for context
        - The full conversation history for better replies
        Returns dict with: root_tweet, article_content, conversation_history, or None if not our conversation.
        """
        parent_id = mention.get("parent_tweet_id")
        if not parent_id:
            return None

        conversation_history = []

        # Check 1: Is the parent one of our original tweets?
        result = await db.execute(
            select(Tweet).where(Tweet.tweet_id == parent_id)
        )
        root_tweet = result.scalar_one_or_none()

        if root_tweet:
            # Direct reply to our tweet
            article_content = None
            if root_tweet.article_id:
                art_result = await db.execute(
                    select(Article).where(Article.id == root_tweet.article_id)
                )
                article_obj = art_result.scalar_one_or_none()
                if article_obj:
                    article_content = article_obj.content

            return {
                "root_tweet": root_tweet,
                "article_content": article_content,
                "conversation_history": [],
            }

        # Check 2: Is the parent one of our replies? (conversation chain)
        result = await db.execute(
            select(Reply).where(Reply.reply_id == parent_id)
        )
        our_reply = result.scalar_one_or_none()

        if our_reply:
            # Someone replied to our reply — trace back to root tweet
            conversation_history.append(f"User @{mention.get('author_username', '?')}: {mention['text']}")
            conversation_history.append(f"Bot: {our_reply.response_text}")
            conversation_history.append(f"User @{our_reply.incoming_user}: {our_reply.incoming_text}")

            # Get the root tweet from the reply's tweet_id (DB foreign key)
            tweet_result = await db.execute(
                select(Tweet).where(Tweet.id == our_reply.tweet_id)
            )
            root_tweet = tweet_result.scalar_one_or_none()

            if root_tweet:
                article_content = None
                if root_tweet.article_id:
                    art_result = await db.execute(
                        select(Article).where(Article.id == root_tweet.article_id)
                    )
                    article_obj = art_result.scalar_one_or_none()
                    if article_obj:
                        article_content = article_obj.content

                return {
                    "root_tweet": root_tweet,
                    "article_content": article_content,
                    "conversation_history": list(reversed(conversation_history)),
                }

        return None

    async def check_and_reply_mentions(self):
        """Check for new mentions, like them, and auto-reply. Follows conversation chains."""
        logger.info("--- MENTION JOB running ---")
        auto_reply = await self._get_setting("auto_reply_enabled", str(self._auto_reply))
        if auto_reply.lower() != "true":
            logger.info("Auto-reply disabled, skipping")
            return

        async with async_session() as db:
            try:
                last_mention_id = await self._get_setting("last_mention_id", None)
                logger.info(f"Checking mentions (since_id={last_mention_id})")

                mentions = await twitter_service.get_mentions(since_id=last_mention_id)

                if not mentions:
                    logger.info("No new mentions found")
                    return

                logger.info(f"Found {len(mentions)} new mentions")

                model = await self._get_ai_model()

                our_user_id = twitter_service._cached_user_id or twitter_service._get_user_id_api()

                for mention in mentions:
                    # Skip our own tweets/replies (don't like or reply to ourselves)
                    if mention.get("author_id") == our_user_id:
                        continue

                    # Skip if we already replied to this mention
                    existing = await db.execute(
                        select(Reply).where(Reply.incoming_reply_id == mention["id"])
                    )
                    if existing.scalar_one_or_none():
                        continue

                    # Like the incoming reply
                    like_result = await twitter_service.like_tweet(mention["id"])
                    if like_result["success"]:
                        logger.info(f"Liked reply from @{mention.get('author_username', '?')}")
                    else:
                        logger.warning(f"Could not like reply: {like_result.get('error', '')[:100]}")

                    # Find conversation context (works for both direct replies and chain replies)
                    context = await self._find_conversation_context(mention, db)

                    if not context:
                        # Not part of our conversation, skip
                        continue

                    root_tweet = context["root_tweet"]
                    article_content = context["article_content"]
                    conversation_history = context["conversation_history"]

                    # Build the prompt with conversation history for better context
                    original_tweet_text = root_tweet.content
                    incoming_text = mention["text"]

                    # If there's conversation history, include it for richer replies
                    if conversation_history:
                        conv_str = "\n".join(conversation_history)
                        incoming_text = f"""[Conversation thread so far]:
{conv_str}

[Latest reply from @{mention.get('author_username', '?')}]:
{mention['text']}"""

                    # Generate reply
                    reply_text = await ai_service.generate_reply(
                        original_tweet=original_tweet_text,
                        incoming_reply=incoming_text,
                        reply_user=mention.get("author_username", "unknown"),
                        article_content=article_content,
                        model=model,
                    )

                    if len(reply_text) > 800:
                        reply_text = reply_text[:797] + "..."

                    # Save reply to DB
                    reply = Reply(
                        tweet_id=root_tweet.id,
                        incoming_text=mention["text"],
                        incoming_user=mention.get("author_username", "unknown"),
                        incoming_reply_id=mention["id"],
                        response_text=reply_text,
                        ai_model_used=model,
                        status="pending",
                    )
                    db.add(reply)
                    await db.commit()
                    await db.refresh(reply)

                    # Post reply (reply to the mention's tweet, not the original)
                    result = await twitter_service.post_reply(
                        reply_text, mention["id"], db, reply.id
                    )

                    if result["success"]:
                        log = ActivityLog(
                            action="auto_reply_posted",
                            details=f"Replied to @{mention.get('author_username', '?')}: {reply_text[:100]}...",
                            status="success",
                        )
                    else:
                        log = ActivityLog(
                            action="auto_reply_failed",
                            details=f"Failed to reply to @{mention.get('author_username', '?')}: {result.get('error', '')[:150]}",
                            status="error",
                        )
                    db.add(log)

                # Update last mention ID (mentions are returned newest-first)
                if mentions:
                    latest_id = mentions[0]["id"]
                    result = await db.execute(
                        select(BotSettings).where(BotSettings.key == "last_mention_id")
                    )
                    setting = result.scalar_one_or_none()
                    if setting:
                        setting.value = latest_id
                    else:
                        db.add(BotSettings(key="last_mention_id", value=latest_id))

                await db.commit()

            except Exception as e:
                logger.error(f"MENTION JOB ERROR: {e}", exc_info=True)
                log = ActivityLog(
                    action="auto_reply_error",
                    details=f"Error checking mentions: {str(e)}",
                    status="error",
                )
                db.add(log)
                await db.commit()

    async def fetch_arxiv_papers(self):
        """Fetch new papers from ArXiv, score them, and import top ones."""
        logger.info("=== ARXIV FETCH JOB STARTED ===")
        async with async_session() as db:
            try:
                imported = await arxiv_service.fetch_and_import(
                    db, max_papers=6, min_score=6.0
                )
                logger.info(f"ArXiv fetch complete: {len(imported)} papers imported")
            except Exception as e:
                logger.error(f"ARXIV JOB ERROR: {e}", exc_info=True)
                log = ActivityLog(
                    action="arxiv_fetch_error",
                    details=f"Error fetching ArXiv papers: {str(e)[:200]}",
                    status="error",
                )
                db.add(log)
                await db.commit()

    async def gtm_tweet_job(self):
        """Strategy-driven GTM tweet: ask the strategy engine what to post, then post it."""
        logger.info("=== GTM TWEET JOB STARTED ===")
        async with async_session() as db:
            try:
                decision = await strategy_engine.decide_content(db)
                content_type = decision.get("content_type", "educational")
                custom_topic = decision.get("specific_topic")

                tweet = await gtm_service.generate_gtm_tweet(content_type, db, custom_topic=custom_topic)
                logger.info("GTM tweet #%s [%s] topic=%s: %s",
                           tweet.id, content_type, (custom_topic or "auto")[:40], tweet.content[:80])

                include_visual = decision.get("include_visual", False)
                visual_type = decision.get("visual_type", "infographic")
                visual_concept = decision.get("visual_concept", "")

                if include_visual and visual_concept:
                    try:
                        logger.info("Generating AI visual: type=%s concept=%s", visual_type, visual_concept[:60])
                        png = await visual_engine.generate_tweet_visual(visual_type, visual_concept)
                        if png:
                            filepath = await visual_engine.save_visual(png, f"gtm_{visual_type}")
                            tweet.media_url = filepath
                            await db.commit()
                            logger.info("AI visual saved: %s (%d bytes)", filepath, len(png))
                    except Exception as ve:
                        logger.warning("AI visual generation failed: %s", ve)
                elif content_type == "showcase":
                    try:
                        from app.models import RLEnvironment, TrainingRun, ResearchPaper

                        env_count = (await db.execute(
                            select(func.count(RLEnvironment.id)).where(RLEnvironment.status == "published")
                        )).scalar() or 0
                        agent_count = (await db.execute(
                            select(func.count(TrainingRun.id)).where(TrainingRun.status == "completed")
                        )).scalar() or 0
                        paper_count = (await db.execute(
                            select(func.count(ResearchPaper.id))
                        )).scalar() or 0

                        png = await visual_engine.generate_stats_card(env_count, agent_count, paper_count)
                        if png:
                            filepath = await visual_engine.save_visual(png, "stats")
                            tweet.media_url = filepath
                            await db.commit()
                    except Exception as ve:
                        logger.warning("Visual generation for showcase tweet failed: %s", ve)

                media_ids = []
                if tweet.media_url:
                    try:
                        with open(tweet.media_url, "rb") as f:
                            img_bytes = f.read()
                        mid = await kualia_twitter_service.upload_media(img_bytes)
                        if mid:
                            media_ids.append(mid)
                    except Exception as me:
                        logger.warning("Media upload failed: %s", me)

                if media_ids:
                    result = await kualia_twitter_service.post_tweet_with_media(
                        tweet.content, media_ids, db, tweet.id
                    )
                else:
                    result = await kualia_twitter_service.post_tweet(tweet.content, db, tweet.id)
                    if result.get("success"):
                        tweet.tweet_id = result["tweet_id"]
                        tweet.status = "posted"
                        tweet.posted_at = datetime.utcnow()

                if result.get("success"):
                    logger.info("GTM tweet #%s posted: %s", tweet.id, result.get("tweet_id"))
                    db.add(ActivityLog(action="gtm_tweet_posted", details=f"[GTM {content_type}] {tweet.content[:100]}", status="success"))
                else:
                    tweet.status = "failed"
                    logger.warning("GTM tweet #%s post failed: %s", tweet.id, result.get("error", ""))
                    db.add(ActivityLog(action="gtm_tweet_failed", details=f"[GTM] Failed: {result.get('error', '')[:150]}", status="error"))

                await db.commit()

                # --- Strategy-driven engagement pass (max 2x/day) ---
                try:
                    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                    engagement_runs_today = (await db.execute(
                        select(func.count(ActivityLog.id)).where(
                            ActivityLog.action == "gtm_engagement",
                            ActivityLog.created_at >= today_start,
                        )
                    )).scalar() or 0

                    if engagement_runs_today < 2:
                        eng_decision = await strategy_engine.decide_engagement(db)
                        custom_queries = eng_decision.get("search_queries", [])
                        if custom_queries:
                            engagement_service.override_queries = custom_queries

                        engage_result = await engagement_service.engage_prospects(db, max_actions=10)
                        discover_result = await engagement_service.discover_prospects(db, max_results=10)

                        engagement_service.override_queries = None

                        details = (
                            f"Liked {engage_result.get('liked', 0)}, "
                            f"Replies {engage_result.get('reply_suggestions', 0)}, "
                            f"Prospects {discover_result.get('discovered', 0)} "
                            f"[focus: {eng_decision.get('focus', 'general')}]"
                        )
                        db.add(ActivityLog(action="gtm_engagement", details=details, status="success"))
                        await db.commit()
                        logger.info("Engagement pass: %s", details)
                    else:
                        logger.info("Engagement pass skipped (already ran %d/2 today)", engagement_runs_today)
                except Exception as eng_err:
                    logger.warning("Engagement pass error (non-fatal): %s", eng_err)

            except Exception as e:
                logger.error("GTM TWEET JOB ERROR: %s", e, exc_info=True)
                db.add(ActivityLog(action="gtm_tweet_error", details=f"Error: {str(e)[:200]}", status="error"))
                await db.commit()

    async def gtm_evaluation_job(self):
        """Weekly strategy review — AI reviews KPIs, decides to continue/adjust/pivot."""
        logger.info("=== GTM STRATEGY REVIEW STARTED ===")
        async with async_session() as db:
            try:
                result = await strategy_engine.review_strategy(db)
                verdict = result.get("verdict", "unknown")
                score = result.get("score", 0)
                summary = f"Verdict: {verdict}, Score: {score}/100"
                logger.info("Strategy review complete: %s", summary)
                db.add(ActivityLog(action="gtm_strategy_review", details=summary, status="success"))
                await db.commit()
            except Exception as e:
                logger.error("GTM STRATEGY REVIEW ERROR: %s", e, exc_info=True)
                db.add(ActivityLog(action="gtm_strategy_review_error", details=f"Error: {str(e)[:200]}", status="error"))
                await db.commit()

    async def showcase_job(self):
        """Generate a showcase tweet with a visual from platform data."""
        logger.info("=== SHOWCASE JOB STARTED ===")
        async with async_session() as db:
            try:
                tweet = await gtm_service.generate_gtm_tweet("showcase", db)

                from app.models import RLEnvironment, TrainingRun, ResearchPaper
                env_count = (await db.execute(
                    select(func.count(RLEnvironment.id)).where(RLEnvironment.status == "published")
                )).scalar() or 0
                agent_count = (await db.execute(
                    select(func.count(TrainingRun.id)).where(TrainingRun.status == "completed")
                )).scalar() or 0
                paper_count = (await db.execute(
                    select(func.count(ResearchPaper.id))
                )).scalar() or 0

                png = await visual_engine.generate_stats_card(env_count, agent_count, paper_count)
                if png:
                    mid = await kualia_twitter_service.upload_media(png)
                    if mid:
                        result = await kualia_twitter_service.post_tweet_with_media(
                            tweet.content, [mid], db, tweet.id
                        )
                        if result.get("success"):
                            logger.info("Showcase tweet posted with visual: %s", result.get("tweet_id"))
                            db.add(ActivityLog(action="showcase_posted", details=f"Showcase: {tweet.content[:100]}", status="success"))
                        else:
                            tweet.status = "failed"
                            db.add(ActivityLog(action="showcase_failed", details=f"Failed: {result.get('error', '')[:150]}", status="error"))
                        await db.commit()
                        return

                result = await kualia_twitter_service.post_tweet(tweet.content, db, tweet.id)
                if result.get("success"):
                    tweet.tweet_id = result["tweet_id"]
                    tweet.status = "posted"
                    tweet.posted_at = datetime.utcnow()
                    db.add(ActivityLog(action="showcase_posted", details=f"Showcase (no visual): {tweet.content[:100]}", status="success"))
                else:
                    tweet.status = "failed"
                    db.add(ActivityLog(action="showcase_failed", details=f"Failed: {result.get('error', '')[:150]}", status="error"))
                await db.commit()

            except Exception as e:
                logger.error("SHOWCASE JOB ERROR: %s", e, exc_info=True)
                db.add(ActivityLog(action="showcase_error", details=f"Error: {str(e)[:200]}", status="error"))
                await db.commit()

    async def fetch_classic_papers(self):
        """Fetch notable AI papers from the last 10 years."""
        logger.info("=== CLASSIC PAPERS FETCH JOB STARTED ===")
        async with async_session() as db:
            try:
                imported = await arxiv_service.fetch_and_import_classics(
                    db, max_papers=3, min_score=7.0
                )
                logger.info(f"Classic papers fetch complete: {len(imported)} papers imported")
            except Exception as e:
                logger.error(f"CLASSICS JOB ERROR: {e}", exc_info=True)
                log = ActivityLog(
                    action="classics_fetch_error",
                    details=f"Error fetching classic papers: {str(e)[:200]}",
                    status="error",
                )
                db.add(log)
                await db.commit()

    async def update_metrics_job(self):
        """Periodically update tweet engagement metrics using batch API."""
        logger.info("--- METRICS JOB running ---")
        async with async_session() as db:
            try:
                await twitter_service.update_tweet_metrics(db)
                logger.info("Metrics batch update completed")
            except Exception as e:
                logger.error(f"METRICS JOB ERROR: {e}", exc_info=True)
                log = ActivityLog(
                    action="metrics_update_error",
                    details=f"Error updating metrics: {str(e)}",
                    status="error",
                )
                db.add(log)
                await db.commit()

    def start(self):
        """Start the scheduler with all jobs."""
        if self.is_running:
            logger.info("Scheduler already running, skipping start")
            return

        logger.info(f"Starting scheduler (tweet interval: {self._tweet_interval}min)")

        # Tweet posting job - first run after 2 minutes, then every interval
        self.scheduler.add_job(
            self.generate_and_post_tweet,
            IntervalTrigger(minutes=self._tweet_interval),
            id="tweet_job",
            name="Auto Tweet Poster",
            replace_existing=True,
        )

        # Retry queued tweets (every 30 minutes)
        self.scheduler.add_job(
            self.retry_queued_tweets,
            IntervalTrigger(minutes=30),
            id="retry_job",
            name="Tweet Retry Queue",
            replace_existing=True,
        )

        # Mention checker DISABLED to save API costs (user handles replies manually)
        # self.scheduler.add_job(
        #     self.check_and_reply_mentions,
        #     IntervalTrigger(minutes=15),
        #     id="mention_job",
        #     name="Mention Checker",
        #     replace_existing=True,
        # )

        # Metrics update once daily (saves API reads, 1 batch call per day)
        self.scheduler.add_job(
            self.update_metrics_job,
            IntervalTrigger(hours=24),
            id="metrics_job",
            name="Metrics Updater (Daily)",
            replace_existing=True,
        )

        # ArXiv paper fetch (every 12 hours = twice daily)
        self.scheduler.add_job(
            self.fetch_arxiv_papers,
            IntervalTrigger(hours=12),
            id="arxiv_job",
            name="ArXiv Paper Fetcher",
            replace_existing=True,
        )

        # Classic AI papers fetch (every 24 hours, notable papers from last 10 years)
        self.scheduler.add_job(
            self.fetch_classic_papers,
            IntervalTrigger(hours=24),
            id="classics_job",
            name="Classic AI Paper Fetcher",
            replace_existing=True,
        )

        # GTM Marketing: auto-tweet every 8 hours (3 per day)
        self.scheduler.add_job(
            self.gtm_tweet_job,
            IntervalTrigger(hours=8),
            id="gtm_tweet_job",
            name="GTM Tweet Poster (8h)",
            replace_existing=True,
        )

        # GTM Showcase: daily showcase tweet with visual
        self.scheduler.add_job(
            self.showcase_job,
            IntervalTrigger(hours=24),
            id="showcase_job",
            name="GTM Showcase Tweet (Daily)",
            replace_existing=True,
        )

        # GTM Evaluation: weekly strategy report
        self.scheduler.add_job(
            self.gtm_evaluation_job,
            IntervalTrigger(hours=168),
            id="gtm_evaluation_job",
            name="GTM Weekly Evaluation",
            replace_existing=True,
        )

        # Email Marketing: weekly tips email
        self.scheduler.add_job(
            self.email_weekly_tips_job,
            IntervalTrigger(hours=168),
            id="email_tips_job",
            name="Email Weekly Tips",
            replace_existing=True,
        )

        # Email Marketing: re-engagement check every 3 days
        self.scheduler.add_job(
            self.email_reengagement_job,
            IntervalTrigger(hours=72),
            id="email_reengagement_job",
            name="Email Re-engagement Check",
            replace_existing=True,
        )

        # Email Marketing: performance evaluation weekly
        self.scheduler.add_job(
            self.email_evaluation_job,
            IntervalTrigger(hours=168),
            id="email_eval_job",
            name="Email Performance Eval",
            replace_existing=True,
        )

        self.scheduler.start()
        self.is_running = True

        logger.info("Scheduler started with all jobs:")
        for job in self.scheduler.get_jobs():
            logger.info(f"  Job: {job.id} -> next run: {job.next_run_time}")

    # ── Email Marketing Agent Jobs ──

    async def email_weekly_tips_job(self):
        """Generate and send AI-written weekly RL tip email."""
        from app.services.agent_registry import agent_registry
        if not agent_registry.get_param("email_marketing", "auto_tips", True):
            logger.info("[EmailAgent] Auto tips disabled, skipping")
            return
        try:
            from app.services.email_marketing_service import email_marketing_agent
            result = await email_marketing_agent.generate_tips_campaign()
            logger.info("[EmailAgent] Tips result: %s", result)
        except Exception as e:
            logger.error("[EmailAgent] Tips job failed: %s", e)

    async def email_reengagement_job(self):
        """Check for inactive users and send re-engagement emails."""
        from app.services.agent_registry import agent_registry
        if not agent_registry.get_param("email_marketing", "auto_reengagement", True):
            logger.info("[EmailAgent] Auto re-engagement disabled, skipping")
            return
        try:
            from app.services.email_marketing_service import email_marketing_agent
            result = await email_marketing_agent.run_reengagement_check()
            logger.info("[EmailAgent] Re-engagement result: %s", result)
        except Exception as e:
            logger.error("[EmailAgent] Re-engagement job failed: %s", e)

    async def email_evaluation_job(self):
        """Evaluate email campaign performance and log insights."""
        from app.services.agent_registry import agent_registry
        if not agent_registry.get_param("email_marketing", "auto_evaluate", True):
            logger.info("[EmailAgent] Auto evaluation disabled, skipping")
            return
        try:
            from app.services.email_marketing_service import email_marketing_agent
            result = await email_marketing_agent.evaluate_performance()
            logger.info("[EmailAgent] Evaluation: %s", str(result)[:500])
        except Exception as e:
            logger.error("[EmailAgent] Evaluation job failed: %s", e)

    async def run_initial_jobs(self):
        """Run retry and arxiv fetch on startup. Metrics run once daily to save API reads."""
        logger.info("Running initial jobs after startup...")
        try:
            await self.retry_queued_tweets()
        except Exception as e:
            logger.error(f"Initial retry job error: {e}")
        try:
            await self.fetch_arxiv_papers()
        except Exception as e:
            logger.error(f"Initial ArXiv fetch error: {e}")

    def stop(self):
        """Stop the scheduler."""
        if self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False

    def update_tweet_interval(self, minutes: int):
        """Update the tweet posting interval."""
        self._tweet_interval = minutes
        if self.is_running:
            self.scheduler.reschedule_job(
                "tweet_job",
                trigger=IntervalTrigger(minutes=minutes),
            )

    def get_status(self) -> dict:
        """Get scheduler status."""
        jobs = []
        if self.is_running:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": str(job.next_run_time) if job.next_run_time else None,
                })

        return {
            "is_running": self.is_running,
            "tweet_interval_minutes": self._tweet_interval,
            "jobs": jobs,
        }


scheduler_service = SchedulerService()
