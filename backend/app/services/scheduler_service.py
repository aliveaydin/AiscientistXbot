import asyncio
import logging
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, func
from app.database import async_session
from app.models import Tweet, Reply, Article, ActivityLog, BotSettings, BlogPost
from app.services.ai_service import ai_service
from app.services.twitter_service import twitter_service
from app.services.article_service import ArticleService
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

    async def generate_and_post_tweet(self):
        """Main job: Pick an article intelligently, generate a unique tweet, and post it."""
        logger.info("=== TWEET JOB STARTED ===")
        async with async_session() as db:
            try:
                await ArticleService.scan_and_import_articles(db)

                article = await ArticleService.get_least_tweeted_article(db)

                if not article:
                    logger.warning("No articles available for tweet generation")
                    log = ActivityLog(
                        action="tweet_skipped",
                        details="No articles available for tweet generation",
                        status="warning",
                    )
                    db.add(log)
                    await db.commit()
                    return

                logger.info(f"Selected article: #{article.id} - {article.title[:60]}")

                # Get previous tweets about this article to avoid repetition
                prev_result = await db.execute(
                    select(Tweet.content).where(Tweet.article_id == article.id)
                )
                previous_tweets = [row[0] for row in prev_result.fetchall()]

                # Get AI model
                model = await self._get_ai_model()

                # Generate tweet with awareness of previous tweets
                tweet_content = await ai_service.generate_tweet(
                    article, model=model, previous_tweets=previous_tweets
                )

                if len(tweet_content) > 500:
                    tweet_content = tweet_content[:497] + "..."

                # Save EN tweet to DB as "queued"
                tweet = Tweet(
                    content=tweet_content,
                    article_id=article.id,
                    ai_model_used=model,
                    status="queued",
                    language="en",
                )
                db.add(tweet)
                await db.commit()
                await db.refresh(tweet)

                logger.info(f"Generated EN tweet ({len(tweet_content)} chars): {tweet_content[:80]}...")

                post_result = await twitter_service.post_tweet(tweet_content, db, tweet.id)
                en_posted = post_result["success"]

                if en_posted:
                    logger.info(f"EN tweet posted successfully: {post_result.get('tweet_id', '?')}")
                    log = ActivityLog(
                        action="auto_tweet_posted",
                        details=f"[EN] Posted: {tweet_content[:100]}...",
                        status="success",
                    )
                else:
                    logger.warning(f"EN tweet failed, will retry: {post_result.get('error', '')[:100]}")
                    log = ActivityLog(
                        action="tweet_retry_pending",
                        details=f"[EN] Queued for retry: {post_result.get('error', '')[:150]}",
                        status="warning",
                    )
                    await db.refresh(tweet)
                    if tweet.status == "failed":
                        tweet.status = "queued"
                db.add(log)
                await db.commit()

                try:
                    tr_content = await ai_service.translate_tweet_to_turkish(
                        tweet_content, model=model
                    )
                    if len(tr_content) > 500:
                        tr_content = tr_content[:497] + "..."

                    tr_tweet = Tweet(
                        content=tr_content,
                        article_id=article.id,
                        ai_model_used=model,
                        status="queued",
                        language="tr",
                        parent_tweet_db_id=tweet.id,
                    )
                    db.add(tr_tweet)
                    await db.commit()
                    await db.refresh(tr_tweet)

                    # Post TR tweet
                    tr_result = await twitter_service.post_tweet(tr_content, db, tr_tweet.id)
                    if tr_result["success"]:
                        log_tr = ActivityLog(
                            action="auto_tweet_posted",
                            details=f"[TR] Posted: {tr_content[:100]}...",
                            status="success",
                        )
                    else:
                        log_tr = ActivityLog(
                            action="tweet_retry_pending",
                            details=f"[TR] Queued for retry: {tr_result.get('error', '')[:150]}",
                            status="warning",
                        )
                        await db.refresh(tr_tweet)
                        if tr_tweet.status == "failed":
                            tr_tweet.status = "queued"
                    db.add(log_tr)
                    await db.commit()
                except Exception as tr_err:
                    logger.error(f"TR tweet error: {tr_err}")
                    log_tr = ActivityLog(
                        action="tr_tweet_error",
                        details=f"Failed to generate/post TR tweet: {str(tr_err)[:200]}",
                        status="error",
                    )
                    db.add(log_tr)
                    await db.commit()

                # Generate blog articles (EN + TR)
                try:
                    logger.info("Generating blog articles...")
                    en_blog = await ai_service.generate_blog_post(
                        article, tweet_content, language="en", model=model
                    )
                    blog_en = BlogPost(
                        tweet_id=tweet.id,
                        article_id=article.id,
                        title=en_blog["title"],
                        content=en_blog["content"],
                        language="en",
                        ai_model_used=model,
                        status="draft",
                    )
                    db.add(blog_en)

                    tr_blog = await ai_service.generate_blog_post(
                        article, tweet_content, language="tr", model=model
                    )
                    blog_tr = BlogPost(
                        tweet_id=tweet.id,
                        article_id=article.id,
                        title=tr_blog["title"],
                        content=tr_blog["content"],
                        language="tr",
                        ai_model_used=model,
                        status="draft",
                    )
                    db.add(blog_tr)
                    await db.commit()

                    logger.info(f"Blog articles generated: EN='{en_blog['title'][:50]}', TR='{tr_blog['title'][:50]}'")
                    log_blog = ActivityLog(
                        action="blog_generated",
                        details=f"Blog articles created: {en_blog['title'][:80]}",
                        status="success",
                    )
                    db.add(log_blog)
                    await db.commit()
                except Exception as blog_err:
                    logger.error(f"Blog generation error: {blog_err}")
                    log_blog = ActivityLog(
                        action="blog_error",
                        details=f"Failed to generate blog: {str(blog_err)[:200]}",
                        status="error",
                    )
                    db.add(log_blog)
                    await db.commit()

                logger.info("=== TWEET JOB FINISHED ===")

            except Exception as e:
                logger.error(f"TWEET JOB ERROR: {e}", exc_info=True)
                log = ActivityLog(
                    action="auto_tweet_error",
                    details=f"Error in auto tweet job: {str(e)}",
                    status="error",
                )
                db.add(log)
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

                for mention in mentions:
                    # Skip if we already replied to this mention
                    existing = await db.execute(
                        select(Reply).where(Reply.incoming_reply_id == mention["id"])
                    )
                    if existing.scalar_one_or_none():
                        continue

                    # Like the incoming reply first
                    like_result = await twitter_service.like_tweet(mention["id"])
                    if like_result["success"]:
                        print(f"[Bot] Liked reply from @{mention.get('author_username', '?')}")
                    else:
                        print(f"[Bot] Could not like reply: {like_result.get('error', '')[:100]}")

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

                    if len(reply_text) > 500:
                        reply_text = reply_text[:497] + "..."

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

        # Mention checking job (every 5 minutes)
        self.scheduler.add_job(
            self.check_and_reply_mentions,
            IntervalTrigger(minutes=5),
            id="mention_job",
            name="Mention Checker",
            replace_existing=True,
        )

        # Metrics update job (every 2 hours, batch API = 1 call per 100 tweets)
        self.scheduler.add_job(
            self.update_metrics_job,
            IntervalTrigger(hours=2),
            id="metrics_job",
            name="Metrics Updater",
            replace_existing=True,
        )

        self.scheduler.start()
        self.is_running = True

        logger.info("Scheduler started with all jobs:")
        for job in self.scheduler.get_jobs():
            logger.info(f"  Job: {job.id} -> next run: {job.next_run_time}")

    async def run_initial_jobs(self):
        """Run metrics and retry immediately after startup."""
        logger.info("Running initial jobs after startup...")
        try:
            await self.update_metrics_job()
        except Exception as e:
            logger.error(f"Initial metrics job error: {e}")
        try:
            await self.retry_queued_tweets()
        except Exception as e:
            logger.error(f"Initial retry job error: {e}")

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
