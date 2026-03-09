import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.database import get_db
from app.models import Tweet, Reply, Article, ActivityLog
from app.schemas import TweetResponse, TweetCreate, GenerateTweetRequest
from app.services.ai_service import ai_service
from app.services.twitter_service import twitter_service
from app.services.article_service import ArticleService
from typing import Optional

logger = logging.getLogger("tweets")

router = APIRouter(prefix="/api/tweets", tags=["Tweets"])


@router.get("/", response_model=list[TweetResponse])
async def get_tweets(
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Get all tweets with optional status filter."""
    query = (
        select(Tweet, Article.title.label("art_title"))
        .outerjoin(Article, Tweet.article_id == Article.id)
        .order_by(Tweet.created_at.desc())
        .limit(limit)
    )
    if status:
        query = query.where(Tweet.status == status)
    result = await db.execute(query)
    rows = result.all()
    tweets = []
    for tweet, art_title in rows:
        data = TweetResponse.model_validate(tweet)
        data.article_title = art_title
        tweets.append(data)
    return tweets


@router.post("/generate", response_model=TweetResponse)
async def generate_tweet(
    request: GenerateTweetRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a tweet using AI from an article."""
    article = None
    if request.article_id:
        article = await ArticleService.get_article_by_id(db, request.article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
    else:
        # Get a random unprocessed article
        article = await ArticleService.get_unprocessed_article(db)
        if not article:
            raise HTTPException(status_code=404, detail="No articles available")

    tweet_content = await ai_service.generate_tweet(
        article, model=request.ai_model, custom_prompt=request.custom_prompt
    )

    if len(tweet_content) > 500:
        tweet_content = tweet_content[:497] + "..."

    tweet = Tweet(
        content=tweet_content,
        article_id=article.id,
        ai_model_used=request.ai_model,
        status="draft",
    )
    db.add(tweet)

    log = ActivityLog(
        action="tweet_generated",
        details=f"Generated tweet with {request.ai_model}: {tweet_content[:100]}...",
        status="success",
    )
    db.add(log)

    await db.commit()
    await db.refresh(tweet)
    return tweet


@router.post("/{tweet_id}/post", response_model=dict)
async def post_tweet(tweet_id: int, db: AsyncSession = Depends(get_db)):
    """Post a draft tweet to Twitter."""
    result = await db.execute(select(Tweet).where(Tweet.id == tweet_id))
    tweet = result.scalar_one_or_none()

    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    if tweet.status == "posted":
        raise HTTPException(status_code=400, detail="Tweet already posted")

    post_result = await twitter_service.post_tweet(tweet.content, db, tweet.id)
    return post_result


@router.post("/{tweet_id}/regenerate", response_model=TweetResponse)
async def regenerate_tweet(
    tweet_id: int,
    ai_model: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Regenerate a tweet with AI."""
    result = await db.execute(select(Tweet).where(Tweet.id == tweet_id))
    tweet = result.scalar_one_or_none()

    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    if not tweet.article_id:
        raise HTTPException(status_code=400, detail="Tweet has no associated article")

    article = await ArticleService.get_article_by_id(db, tweet.article_id)
    model = ai_model or tweet.ai_model_used

    new_content = await ai_service.generate_tweet(article, model=model)
    if len(new_content) > 500:
        new_content = new_content[:497] + "..."

    tweet.content = new_content
    tweet.ai_model_used = model
    tweet.status = "draft"

    await db.commit()
    await db.refresh(tweet)
    return tweet


@router.put("/{tweet_id}", response_model=TweetResponse)
async def update_tweet(
    tweet_id: int,
    data: TweetCreate,
    db: AsyncSession = Depends(get_db),
):
    """Manually edit a tweet."""
    result = await db.execute(select(Tweet).where(Tweet.id == tweet_id))
    tweet = result.scalar_one_or_none()

    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    if tweet.status == "posted":
        raise HTTPException(status_code=400, detail="Cannot edit a posted tweet")

    tweet.content = data.content
    await db.commit()
    await db.refresh(tweet)
    return tweet


@router.delete("/{tweet_id}")
async def delete_tweet(tweet_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a draft tweet."""
    result = await db.execute(select(Tweet).where(Tweet.id == tweet_id))
    tweet = result.scalar_one_or_none()

    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    if tweet.status == "posted":
        raise HTTPException(status_code=400, detail="Cannot delete a posted tweet")

    await db.delete(tweet)
    await db.commit()
    return {"message": "Tweet deleted"}


# ─── Local Poster Agent Endpoints ────────────────────────────────────

@router.get("/queue/pending")
async def get_pending_tweets(db: AsyncSession = Depends(get_db)):
    """Get tweets queued for posting (used by local poster agent)."""
    result = await db.execute(
        select(Tweet)
        .where(Tweet.status.in_(["queued", "draft"]))
        .order_by(Tweet.created_at.asc())
    )
    tweets = result.scalars().all()
    return [
        {
            "id": t.id,
            "content": t.content,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tweets
    ]


@router.post("/{tweet_id}/confirm-posted")
async def confirm_tweet_posted(
    tweet_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """Mark a tweet as posted (called by local poster agent after successful Twitter post)."""
    result = await db.execute(select(Tweet).where(Tweet.id == tweet_id))
    tweet = result.scalar_one_or_none()

    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    twitter_tweet_id = data.get("tweet_id", "")
    tweet.tweet_id = twitter_tweet_id
    tweet.status = "posted"
    tweet.posted_at = datetime.utcnow()

    log = ActivityLog(
        action="tweet_posted",
        details=f"Posted via local agent: {tweet.content[:100]}... (ID: {twitter_tweet_id})",
        status="success",
    )
    db.add(log)
    await db.commit()

    return {"success": True, "message": f"Tweet {tweet_id} marked as posted"}


@router.post("/{tweet_id}/mark-failed")
async def mark_tweet_failed(
    tweet_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """Mark a tweet as failed (called by local poster agent on failure)."""
    result = await db.execute(select(Tweet).where(Tweet.id == tweet_id))
    tweet = result.scalar_one_or_none()

    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    tweet.status = "failed"
    error = data.get("error", "Unknown error")

    log = ActivityLog(
        action="tweet_failed",
        details=f"Local agent failed: {error}",
        status="error",
    )
    db.add(log)
    await db.commit()

    return {"success": True, "message": f"Tweet {tweet_id} marked as failed"}


@router.post("/translate-and-post-all-tr")
async def translate_and_post_all_turkish(db: AsyncSession = Depends(get_db)):
    """Generate Turkish translations for all posted EN tweets that don't have a TR version yet, and post them."""
    # Get all posted EN tweets
    result = await db.execute(
        select(Tweet).where(
            Tweet.status == "posted",
            Tweet.tweet_id.isnot(None),
            Tweet.language.in_(["en", None]),
        ).order_by(Tweet.created_at.asc())
    )
    en_tweets = result.scalars().all()

    translated = 0
    failed = 0

    for en_tweet in en_tweets:
        # Check if TR version already exists
        existing = await db.execute(
            select(Tweet).where(Tweet.parent_tweet_db_id == en_tweet.id)
        )
        if existing.scalar_one_or_none():
            continue  # Already has TR version

        try:
            # Generate Turkish translation
            tr_content = await ai_service.translate_tweet_to_turkish(
                en_tweet.content, model=en_tweet.ai_model_used
            )
            if len(tr_content) > 500:
                tr_content = tr_content[:497] + "..."

            # Save TR tweet
            tr_tweet = Tweet(
                content=tr_content,
                article_id=en_tweet.article_id,
                ai_model_used=en_tweet.ai_model_used,
                status="queued",
                language="tr",
                parent_tweet_db_id=en_tweet.id,
            )
            db.add(tr_tweet)
            await db.commit()
            await db.refresh(tr_tweet)

            # Post TR tweet
            post_result = await twitter_service.post_tweet(tr_content, db, tr_tweet.id)
            if post_result["success"]:
                translated += 1
                log = ActivityLog(
                    action="tr_tweet_posted",
                    details=f"[TR] Posted translation of tweet #{en_tweet.id}: {tr_content[:80]}...",
                    status="success",
                )
            else:
                failed += 1
                # Keep as queued for retry
                await db.refresh(tr_tweet)
                if tr_tweet.status == "failed":
                    tr_tweet.status = "queued"
                log = ActivityLog(
                    action="tr_tweet_queued",
                    details=f"[TR] Queued for retry: {post_result.get('error', '')[:150]}",
                    status="warning",
                )
            db.add(log)
            await db.commit()

        except Exception as e:
            failed += 1
            log = ActivityLog(
                action="tr_tweet_error",
                details=f"Failed to translate tweet #{en_tweet.id}: {str(e)[:200]}",
                status="error",
            )
            db.add(log)
            await db.commit()

    return {
        "message": f"Turkish translations: {translated} posted, {failed} failed/queued",
        "translated": translated,
        "failed": failed,
    }


@router.post("/{tweet_id}/auto-reply", response_model=dict)
async def auto_reply_to_tweet(tweet_id: int, db: AsyncSession = Depends(get_db)):
    """Fetch replies to a posted tweet, generate AI replies, and post them."""
    result = await db.execute(select(Tweet).where(Tweet.id == tweet_id))
    tweet = result.scalar_one_or_none()

    if not tweet or not tweet.tweet_id:
        raise HTTPException(status_code=404, detail="Tweet not found or not posted yet")

    if tweet.status != "posted":
        raise HTTPException(status_code=400, detail="Can only reply to posted tweets")

    mentions = await twitter_service.get_mentions()

    our_tweet_ids = {tweet.tweet_id}
    replies_result = await db.execute(
        select(Reply.reply_id).where(
            Reply.tweet_id == tweet.id,
            Reply.reply_id.isnot(None),
        )
    )
    for rid in replies_result.scalars().all():
        our_tweet_ids.add(rid)

    our_user_id = twitter_service._cached_user_id
    if not our_user_id:
        import asyncio
        loop = asyncio.get_event_loop()
        our_user_id = await loop.run_in_executor(
            None, twitter_service._get_user_id_api
        )

    relevant = []
    for m in mentions:
        if m.get("author_id") == our_user_id:
            continue
        if m.get("parent_tweet_id") not in our_tweet_ids:
            continue
        existing = await db.execute(
            select(Reply).where(Reply.incoming_reply_id == m["id"])
        )
        if existing.scalar_one_or_none():
            continue
        relevant.append(m)

    if not relevant:
        return {"message": "No new replies found for this tweet", "replies_posted": 0, "replies": []}

    article = None
    if tweet.article_id:
        article = await ArticleService.get_article_by_id(db, tweet.article_id)

    posted = []
    for mention in relevant:
        try:
            reply_text = await ai_service.generate_reply(
                original_tweet=tweet.content,
                incoming_reply=mention["text"],
                reply_user=mention.get("author_username", "user"),
                article_content=article.content[:2000] if article and article.content else None,
            )

            if len(reply_text) > 500:
                reply_text = reply_text[:497] + "..."

            reply = Reply(
                tweet_id=tweet.id,
                incoming_text=mention["text"],
                incoming_user=mention.get("author_username", "unknown"),
                incoming_reply_id=mention["id"],
                response_text=reply_text,
                ai_model_used="default",
                status="pending",
            )
            db.add(reply)
            await db.commit()
            await db.refresh(reply)

            post_result = await twitter_service.post_reply(
                reply_text, mention["id"], db, reply.id
            )

            if post_result.get("success"):
                posted.append({
                    "mention_author": mention.get("author_username"),
                    "mention_text": mention["text"][:200],
                    "our_reply": reply_text,
                })
                log = ActivityLog(
                    action="manual_reply_posted",
                    details=f"Replied to @{mention.get('author_username', '?')}: {reply_text[:100]}...",
                    status="success",
                )
            else:
                log = ActivityLog(
                    action="manual_reply_failed",
                    details=f"Failed reply to @{mention.get('author_username', '?')}: {post_result.get('error', '')[:150]}",
                    status="error",
                )
            db.add(log)
            await db.commit()

        except Exception as e:
            logger.error(f"Error replying to mention {mention['id']}: {e}")

    return {
        "message": f"Replied to {len(posted)} comment(s)",
        "replies_posted": len(posted),
        "replies": posted,
    }
