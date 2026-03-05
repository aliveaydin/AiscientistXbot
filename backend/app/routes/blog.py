from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import BlogPost, Tweet, Article
from app.services.ai_service import ai_service
from typing import Optional

router = APIRouter(prefix="/api/blog", tags=["Blog"])


@router.get("/")
async def get_blog_posts(
    language: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Get all blog articles."""
    query = select(BlogPost).order_by(BlogPost.created_at.desc()).limit(limit)
    if language:
        query = query.where(BlogPost.language == language)
    result = await db.execute(query)
    posts = result.scalars().all()

    items = []
    for p in posts:
        tweet_content = None
        article_title = None
        if p.tweet_id:
            t = await db.execute(select(Tweet.content).where(Tweet.id == p.tweet_id))
            row = t.first()
            if row:
                tweet_content = row[0]
        if p.article_id:
            a = await db.execute(select(Article.title, Article.filename).where(Article.id == p.article_id))
            row = a.first()
            if row:
                article_title = row[0] or row[1]

        items.append({
            "id": p.id,
            "tweet_id": p.tweet_id,
            "article_id": p.article_id,
            "title": p.title,
            "content": p.content,
            "language": p.language,
            "ai_model_used": p.ai_model_used,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "tweet_content": tweet_content,
            "article_title": article_title,
        })

    return items


@router.get("/{post_id}")
async def get_blog_post(post_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single blog article."""
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")

    tweet_content = None
    article_title = None
    if post.tweet_id:
        t = await db.execute(select(Tweet.content).where(Tweet.id == post.tweet_id))
        row = t.first()
        if row:
            tweet_content = row[0]
    if post.article_id:
        a = await db.execute(select(Article.title, Article.filename).where(Article.id == post.article_id))
        row = a.first()
        if row:
            article_title = row[0] or row[1]

    return {
        "id": post.id,
        "tweet_id": post.tweet_id,
        "article_id": post.article_id,
        "title": post.title,
        "content": post.content,
        "language": post.language,
        "ai_model_used": post.ai_model_used,
        "status": post.status,
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "tweet_content": tweet_content,
        "article_title": article_title,
    }


@router.put("/{post_id}/status")
async def update_blog_status(
    post_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """Update blog post status (draft -> published)."""
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")

    post.status = data.get("status", post.status)
    await db.commit()
    return {"success": True, "status": post.status}


@router.post("/generate-from-tweet/{tweet_db_id}")
async def generate_blog_from_tweet(tweet_db_id: int, db: AsyncSession = Depends(get_db)):
    """Generate EN + TR blog articles from an existing tweet."""
    result = await db.execute(select(Tweet).where(Tweet.id == tweet_db_id))
    tweet = result.scalar_one_or_none()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    if not tweet.article_id:
        raise HTTPException(status_code=400, detail="Tweet has no linked source paper")

    art_result = await db.execute(select(Article).where(Article.id == tweet.article_id))
    article = art_result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Source paper not found")

    created = []
    for lang in ["en", "tr"]:
        blog_data = await ai_service.generate_blog_post(
            article, tweet.content, language=lang, model=tweet.ai_model_used
        )
        post = BlogPost(
            tweet_id=tweet.id,
            article_id=article.id,
            title=blog_data["title"],
            content=blog_data["content"],
            language=lang,
            ai_model_used=blog_data.get("model", tweet.ai_model_used),
            status="draft",
        )
        db.add(post)
        created.append({"language": lang, "title": blog_data["title"], "model": blog_data.get("model", "?")})

    await db.commit()
    return {"success": True, "created": created}


@router.delete("/{post_id}")
async def delete_blog_post(post_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a blog post."""
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")

    await db.delete(post)
    await db.commit()
    return {"message": "Blog post deleted"}
