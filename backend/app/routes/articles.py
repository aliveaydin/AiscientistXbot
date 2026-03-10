from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import Article, Tweet
from app.schemas import ArticleResponse, ArticleListResponse
from app.services.article_service import ArticleService
from app.services.ai_service import ai_service
from typing import Optional

router = APIRouter(prefix="/api/articles", tags=["Articles"])


@router.get("/", response_model=list[ArticleListResponse])
async def get_articles(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Get articles with pagination."""
    result = await db.execute(
        select(
            Article,
            func.count(Tweet.id).label("tweet_count"),
        )
        .outerjoin(Tweet, Tweet.article_id == Article.id)
        .group_by(Article.id)
        .order_by(Article.added_at.desc())
        .offset(offset)
        .limit(limit)
    )

    articles = []
    for row in result.all():
        article = row[0]
        tweet_count = row[1]
        articles.append(
            ArticleListResponse(
                id=article.id,
                filename=article.filename,
                title=article.title,
                file_type=article.file_type,
                added_at=article.added_at,
                is_processed=article.is_processed,
                tweet_count=tweet_count,
                source=article.source or "manual",
                arxiv_id=article.arxiv_id,
                arxiv_url=article.arxiv_url,
                relevance_score=article.relevance_score,
            )
        )
    return articles


@router.get("/count")
async def get_article_count(db: AsyncSession = Depends(get_db)):
    """Get total article count for pagination."""
    result = await db.execute(select(func.count(Article.id)))
    return {"count": result.scalar() or 0}


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """Get article details."""
    article = await ArticleService.get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.post("/upload", response_model=ArticleResponse)
async def upload_article(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a new article."""
    from pathlib import Path

    ext = Path(file.filename).suffix.lower()
    if ext not in ArticleService.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(ArticleService.SUPPORTED_EXTENSIONS)}",
        )

    content = await file.read()
    article = await ArticleService.upload_article(db, file.filename, content)
    return article


@router.post("/scan")
async def scan_articles(db: AsyncSession = Depends(get_db)):
    """Scan articles directory for new articles."""
    imported = await ArticleService.scan_and_import_articles(db)
    return {
        "message": f"Imported {len(imported)} new articles",
        "articles": [{"id": a.id, "filename": a.filename} for a in imported],
    }


@router.post("/{article_id}/summarize")
async def summarize_article(
    article_id: int,
    ai_model: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Generate a summary of an article."""
    article = await ArticleService.get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    insights = await ai_service.summarize_article(article, model=ai_model)

    # Save summary
    article.summary = "\n".join(f"- {insight}" for insight in insights)
    await db.commit()

    return {"insights": insights, "summary": article.summary}


@router.post("/fetch-arxiv")
async def fetch_arxiv(db: AsyncSession = Depends(get_db)):
    """Manually trigger ArXiv paper fetch."""
    from app.services.arxiv_service import arxiv_service
    imported = await arxiv_service.fetch_and_import(db, max_papers=3, min_score=6.0)
    return {
        "message": f"Fetched and imported {len(imported)} papers from ArXiv",
        "papers": [
            {
                "id": a.id,
                "title": a.title,
                "arxiv_id": a.arxiv_id,
                "score": a.relevance_score,
            }
            for a in imported
        ],
    }


@router.delete("/{article_id}")
async def delete_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an article."""
    article = await ArticleService.get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    await db.delete(article)
    await db.commit()
    return {"message": "Article deleted"}
