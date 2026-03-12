from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.database import get_db
from app.models import ResearchPaper, BlogPost, RLEnvironment

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/papers")
async def get_published_papers(limit: int = 20, offset: int = 0, db: AsyncSession = Depends(get_db)):
    """Get published research papers for public website."""
    query = select(ResearchPaper).where(ResearchPaper.published == True).order_by(desc(ResearchPaper.published_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    papers = result.scalars().all()

    count_query = select(func.count()).select_from(ResearchPaper).where(ResearchPaper.published == True)
    total = (await db.execute(count_query)).scalar()

    return {
        "items": [
            {
                "id": p.id,
                "title": p.title,
                "abstract": p.abstract,
                "content": p.content,
                "status": p.status,
                "version": p.version,
                "published_at": p.published_at.isoformat() if p.published_at else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in papers
        ],
        "total": total,
    }


@router.get("/papers/{paper_id}")
async def get_published_paper(paper_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ResearchPaper).where(ResearchPaper.id == paper_id, ResearchPaper.published == True)
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return {
        "id": paper.id,
        "title": paper.title,
        "abstract": paper.abstract,
        "content": paper.content,
        "status": paper.status,
        "version": paper.version,
        "published_at": paper.published_at.isoformat() if paper.published_at else None,
        "created_at": paper.created_at.isoformat() if paper.created_at else None,
    }


@router.get("/blog")
async def get_published_blog(limit: int = 20, offset: int = 0, db: AsyncSession = Depends(get_db)):
    query = select(BlogPost).where(BlogPost.published == True).order_by(desc(BlogPost.published_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    posts = result.scalars().all()

    count_query = select(func.count()).select_from(BlogPost).where(BlogPost.published == True)
    total = (await db.execute(count_query)).scalar()

    return {
        "items": [
            {
                "id": p.id,
                "title": p.title,
                "content": p.content,
                "language": p.language,
                "published_at": p.published_at.isoformat() if p.published_at else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in posts
        ],
        "total": total,
    }


@router.get("/blog/{post_id}")
async def get_published_blog_post(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BlogPost).where(BlogPost.id == post_id, BlogPost.published == True)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "language": post.language,
        "published_at": post.published_at.isoformat() if post.published_at else None,
        "created_at": post.created_at.isoformat() if post.created_at else None,
    }


@router.get("/environments")
async def get_published_environments(
    limit: int = 20, offset: int = 0, category: str = None, db: AsyncSession = Depends(get_db)
):
    query = select(RLEnvironment).where(RLEnvironment.status == "published")
    if category:
        query = query.where(RLEnvironment.category == category)
    query = query.order_by(desc(RLEnvironment.published_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    envs = result.scalars().all()

    count_q = select(func.count()).select_from(RLEnvironment).where(RLEnvironment.status == "published")
    if category:
        count_q = count_q.where(RLEnvironment.category == category)
    total = (await db.execute(count_q)).scalar()

    return {
        "items": [
            {
                "id": e.id,
                "name": e.name,
                "description": e.description,
                "category": e.category,
                "observation_space": e.observation_space,
                "action_space": e.action_space,
                "reward_description": e.reward_description,
                "difficulty": e.difficulty,
                "preview_image": e.preview_image,
                "published_at": e.published_at.isoformat() if e.published_at else None,
            }
            for e in envs
        ],
        "total": total,
    }


@router.get("/environments/{env_id}")
async def get_published_environment(env_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RLEnvironment).where(RLEnvironment.id == env_id, RLEnvironment.status == "published")
    )
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    return {
        "id": env.id,
        "name": env.name,
        "description": env.description,
        "category": env.category,
        "observation_space": env.observation_space,
        "action_space": env.action_space,
        "reward_description": env.reward_description,
        "code": env.code,
        "difficulty": env.difficulty,
        "preview_image": env.preview_image,
        "published_at": env.published_at.isoformat() if env.published_at else None,
        "created_at": env.created_at.isoformat() if env.created_at else None,
    }


@router.get("/stats")
async def get_public_stats(db: AsyncSession = Depends(get_db)):
    papers = (await db.execute(select(func.count()).select_from(ResearchPaper).where(ResearchPaper.published == True))).scalar()
    blogs = (await db.execute(select(func.count()).select_from(BlogPost).where(BlogPost.published == True))).scalar()
    envs = (await db.execute(select(func.count()).select_from(RLEnvironment).where(RLEnvironment.status == "published"))).scalar()
    return {"papers": papers, "blog_posts": blogs, "environments": envs}
