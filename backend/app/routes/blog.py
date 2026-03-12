from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
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
            "published": p.published if hasattr(p, 'published') else False,
            "published_at": p.published_at.isoformat() if hasattr(p, 'published_at') and p.published_at else None,
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

    new_status = data.get("status", post.status)
    post.status = new_status
    if new_status == "published":
        post.published = True
        post.published_at = datetime.utcnow()
    else:
        post.published = False
        post.published_at = None
    await db.commit()
    return {"success": True, "status": post.status, "published": post.published}


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


@router.post("/generate-from-article/{article_id}")
async def generate_blog_from_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """Generate EN + TR blog articles directly from a source article."""
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    created = []
    for lang in ["en", "tr"]:
        blog_data = await ai_service.generate_blog_post(
            article, tweet_content=None, language=lang
        )
        post = BlogPost(
            tweet_id=None,
            article_id=article.id,
            title=blog_data["title"],
            content=blog_data["content"],
            language=lang,
            ai_model_used=blog_data.get("model", "kimi-k2.5"),
            status="draft",
        )
        db.add(post)
        created.append({"language": lang, "title": blog_data["title"], "model": blog_data.get("model", "?")})

    await db.commit()
    return {"success": True, "created": created}


@router.post("/generate-from-topic")
async def generate_blog_from_topic(data: dict, db: AsyncSession = Depends(get_db)):
    """Generate EN + TR blog articles from a research topic. Searches ArXiv for related papers."""
    topic = data.get("topic", "").strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic is required")

    from app.services.lab_service import lab_service

    search_terms = await lab_service._extract_search_terms(topic)
    entries = await lab_service._search_arxiv_by_terms(search_terms, max_results=10)

    ref_context = ""
    imported_ids = []
    existing_q = await db.execute(select(Article.arxiv_id).where(Article.arxiv_id.isnot(None)))
    existing_ids = {row[0] for row in existing_q.fetchall()}

    for entry in entries[:5]:
        ref_context += f"- {entry['title']}: {entry['abstract'][:300]}...\n\n"
        if entry["arxiv_id"] not in existing_ids:
            art = Article(
                filename=f"arxiv_{entry['arxiv_id'].replace('/', '_')}.pdf",
                title=entry["title"],
                content=f"{entry['title']}\n\nAbstract:\n{entry['abstract']}",
                file_type="pdf",
                source="arxiv",
                arxiv_id=entry["arxiv_id"],
                arxiv_url=f"https://arxiv.org/abs/{entry['arxiv_id']}",
                arxiv_categories=", ".join(entry["categories"]),
                is_processed=False,
            )
            db.add(art)
            await db.flush()
            imported_ids.append(art.id)
            existing_ids.add(entry["arxiv_id"])

    created = []
    for lang in ["en", "tr"]:
        blog_data = await ai_service.generate_blog_post(
            article=None, tweet_content=None, language=lang,
            topic=topic, reference_context=ref_context,
        )
        post = BlogPost(
            tweet_id=None,
            article_id=imported_ids[0] if imported_ids else None,
            title=blog_data["title"],
            content=blog_data["content"],
            language=lang,
            ai_model_used=blog_data.get("model", "kimi-k2.5"),
            status="draft",
        )
        db.add(post)
        created.append({"language": lang, "title": blog_data["title"], "model": blog_data.get("model", "?")})

    await db.commit()
    return {
        "success": True,
        "created": created,
        "papers_found": len(entries),
        "papers_imported": len(imported_ids),
    }


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
