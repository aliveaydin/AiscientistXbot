from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.database import get_db
from app.models import Tweet, Article, ActivityLog
from app.schemas import TweetResponse, TweetCreate, GenerateTweetRequest
from app.services.ai_service import ai_service
from app.services.twitter_service import twitter_service
from app.services.article_service import ArticleService
from typing import Optional

router = APIRouter(prefix="/api/tweets", tags=["Tweets"])


@router.get("/", response_model=list[TweetResponse])
async def get_tweets(
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Get all tweets with optional status filter."""
    query = select(Tweet).order_by(Tweet.created_at.desc()).limit(limit)
    if status:
        query = query.where(Tweet.status == status)
    result = await db.execute(query)
    return result.scalars().all()


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

    if len(tweet_content) > 280:
        tweet_content = tweet_content[:277] + "..."

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
    if len(new_content) > 280:
        new_content = new_content[:277] + "..."

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
