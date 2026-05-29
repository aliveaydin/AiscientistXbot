"""
Marketing API routes for GTM agent management.
"""
import json
import logging
import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import (
    MarketingTweet, EngagementLog, Prospect, GTMReport,
    GTMStrategy, GTMDecisionLog, RLEnvironment, TrainingRun, ResearchPaper,
)
from app.services.gtm_service import gtm_service
from app.services.visual_engine import visual_engine
from app.services.engagement_service import engagement_service
from app.services.twitter_service import kualia_twitter_service
from app.services.strategy_engine import strategy_engine
from app.auth import require_admin

logger = logging.getLogger("marketing_routes")

router = APIRouter(prefix="/api/marketing", tags=["marketing"], dependencies=[Depends(require_admin)])


# --- Request Models ---

class GenerateTweetRequest(BaseModel):
    content_type: str = "product"
    custom_topic: Optional[str] = None

class PostTweetRequest(BaseModel):
    pass

class EditTweetRequest(BaseModel):
    content: str

class GenerateVisualRequest(BaseModel):
    template: str = "feature_card"
    data: dict = {}

class AIVisualRequest(BaseModel):
    concept: str
    visual_type: str = "infographic"
    generate_tweet: bool = False

class ReplySuggestionRequest(BaseModel):
    tweet_text: str
    tweet_id: str


# --- Tweet Endpoints ---

@router.get("/tweets")
async def list_marketing_tweets(
    status: Optional[str] = None,
    content_type: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(MarketingTweet).order_by(MarketingTweet.created_at.desc())
    if status:
        query = query.where(MarketingTweet.status == status)
    if content_type:
        query = query.where(MarketingTweet.content_type == content_type)
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    tweets = result.scalars().all()

    count_q = select(func.count(MarketingTweet.id))
    if status:
        count_q = count_q.where(MarketingTweet.status == status)
    if content_type:
        count_q = count_q.where(MarketingTweet.content_type == content_type)
    total = (await db.execute(count_q)).scalar() or 0

    return {
        "tweets": [
            {
                "id": t.id,
                "content": t.content,
                "content_type": t.content_type,
                "ai_model_used": t.ai_model_used,
                "status": t.status,
                "tweet_id": t.tweet_id,
                "media_url": t.media_url,
                "hashtags": t.hashtags,
                "scheduled_for": t.scheduled_for.isoformat() if t.scheduled_for else None,
                "posted_at": t.posted_at.isoformat() if t.posted_at else None,
                "likes": t.likes,
                "retweets": t.retweets,
                "replies_count": t.replies_count,
                "impressions": t.impressions,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tweets
        ],
        "total": total,
    }


@router.post("/tweets/generate")
async def generate_marketing_tweet(
    req: GenerateTweetRequest,
    db: AsyncSession = Depends(get_db),
):
    tweet = await gtm_service.generate_gtm_tweet(
        content_type=req.content_type,
        db=db,
        custom_topic=req.custom_topic,
    )
    return {
        "id": tweet.id,
        "content": tweet.content,
        "content_type": tweet.content_type,
        "status": tweet.status,
        "hashtags": tweet.hashtags,
    }


@router.put("/tweets/{tweet_id}")
async def edit_marketing_tweet(
    tweet_id: int,
    req: EditTweetRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MarketingTweet).where(MarketingTweet.id == tweet_id))
    tweet = result.scalar_one_or_none()
    if not tweet:
        raise HTTPException(404, "Tweet not found")
    if tweet.status == "posted":
        raise HTTPException(400, "Cannot edit posted tweet")
    tweet.content = req.content
    await db.commit()
    return {"id": tweet.id, "content": tweet.content, "status": tweet.status}


@router.post("/tweets/{tweet_id}/post")
async def post_marketing_tweet(
    tweet_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MarketingTweet).where(MarketingTweet.id == tweet_id))
    tweet = result.scalar_one_or_none()
    if not tweet:
        raise HTTPException(404, "Tweet not found")
    if tweet.status == "posted":
        raise HTTPException(400, "Already posted")

    media_ids = []
    if tweet.media_url:
        try:
            import os
            if os.path.exists(tweet.media_url):
                with open(tweet.media_url, "rb") as f:
                    img_bytes = f.read()
                mid = await kualia_twitter_service.upload_media(img_bytes)
                if mid:
                    media_ids.append(mid)
        except Exception as e:
            logger.warning("Media upload for tweet #%s failed: %s", tweet_id, e)

    if media_ids:
        post_result = await kualia_twitter_service.post_tweet_with_media(
            tweet.content, media_ids, db, tweet.id
        )
    else:
        post_result = await kualia_twitter_service.post_tweet(tweet.content, db, tweet.id)
        if post_result["success"]:
            tweet.tweet_id = post_result["tweet_id"]
            tweet.status = "posted"
            tweet.posted_at = datetime.utcnow()
            await db.commit()

    if post_result.get("success"):
        return {"success": True, "tweet_id": post_result.get("tweet_id")}
    else:
        tweet.status = "failed"
        await db.commit()
        raise HTTPException(502, f"Twitter post failed: {post_result.get('error', 'Unknown')}")


@router.delete("/tweets/{tweet_id}")
async def delete_marketing_tweet(
    tweet_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MarketingTweet).where(MarketingTweet.id == tweet_id))
    tweet = result.scalar_one_or_none()
    if not tweet:
        raise HTTPException(404, "Tweet not found")
    await db.delete(tweet)
    await db.commit()
    return {"deleted": True}


# --- Visual Content ---

@router.post("/visual/generate")
async def generate_visual(
    req: GenerateVisualRequest,
    db: AsyncSession = Depends(get_db),
):
    png_bytes = await visual_engine.render_template(req.template, req.data)
    if not png_bytes:
        raise HTTPException(500, "Visual rendering failed")

    import os
    output_dir = os.path.join(os.getenv("DATA_DIR", "./data"), "marketing_visuals")
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{req.template}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "wb") as f:
        f.write(png_bytes)

    return {"path": filepath, "size_bytes": len(png_bytes), "template": req.template}


@router.post("/visual/generate-tweet")
async def generate_visual_tweet(
    req: GenerateVisualRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a tweet with an attached visual card."""
    import os
    png_bytes = await visual_engine.render_template(req.template, req.data)
    if not png_bytes:
        raise HTTPException(500, "Visual rendering failed")

    output_dir = os.path.join(os.getenv("DATA_DIR", "./data"), "marketing_visuals")
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{req.template}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "wb") as f:
        f.write(png_bytes)

    topic = req.data.get("tweet_topic") or req.data.get("TITLE") or req.data.get("BADGE") or "kualia.ai feature"
    tweet = await gtm_service.generate_gtm_tweet("product", db, custom_topic=topic)
    tweet.media_url = filepath
    await db.commit()
    await db.refresh(tweet)

    return {
        "tweet_id": tweet.id,
        "content": tweet.content,
        "media_path": filepath,
        "template": req.template,
        "size_bytes": len(png_bytes),
    }


@router.post("/visual/ai-design")
async def ai_design_visual(
    req: AIVisualRequest,
    db: AsyncSession = Depends(get_db),
):
    """AI designs a custom HTML visual from a concept description, renders to PNG."""
    png_bytes = await visual_engine.design_and_render(req.concept, req.visual_type)
    if not png_bytes:
        raise HTTPException(500, "AI visual design failed")

    filepath = await visual_engine.save_visual(png_bytes, f"ai_{req.visual_type}")

    result = {
        "path": filepath,
        "filename": os.path.basename(filepath),
        "size_bytes": len(png_bytes),
        "visual_type": req.visual_type,
        "concept": req.concept,
    }

    if req.generate_tweet:
        tweet = await gtm_service.generate_gtm_tweet("product", db, custom_topic=req.concept)
        tweet.media_url = filepath
        await db.commit()
        await db.refresh(tweet)
        result["tweet_id"] = tweet.id
        result["tweet_content"] = tweet.content

    return result


@router.post("/visual/screenshot")
async def screenshot_visual(
    path: str = "/",
    selector: Optional[str] = None,
):
    """Capture a screenshot of a kualia.ai page."""
    png_bytes = await visual_engine.screenshot_page(path, selector)
    if not png_bytes:
        raise HTTPException(500, "Screenshot capture failed")

    filepath = await visual_engine.save_visual(png_bytes, "screenshot")
    return {
        "path": filepath,
        "filename": os.path.basename(filepath),
        "size_bytes": len(png_bytes),
        "page": path,
    }


@router.get("/visuals")
async def list_visuals():
    """List all generated marketing visuals."""
    import os, glob as globmod
    output_dir = os.path.join(os.getenv("DATA_DIR", "./data"), "marketing_visuals")
    if not os.path.isdir(output_dir):
        return {"visuals": [], "total": 0}

    files = sorted(globmod.glob(os.path.join(output_dir, "*.png")), key=os.path.getmtime, reverse=True)
    visuals = []
    for f in files[:100]:
        stat = os.stat(f)
        visuals.append({
            "filename": os.path.basename(f),
            "path": f,
            "size_bytes": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return {"visuals": visuals, "total": len(visuals)}


@router.get("/visuals/{filename}")
async def serve_visual(filename: str):
    """Serve a visual image file."""
    import os
    from fastapi.responses import FileResponse
    filepath = os.path.join(os.getenv("DATA_DIR", "./data"), "marketing_visuals", filename)
    if not os.path.exists(filepath):
        raise HTTPException(404, "Visual not found")
    return FileResponse(filepath, media_type="image/png")


# --- Engagement ---

@router.get("/engagement/log")
async def get_engagement_log(
    action_type: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    logs = await engagement_service.get_recent_logs(db, limit=limit, action_type=action_type)
    return {"logs": logs, "total": len(logs)}


@router.post("/engagement/search-and-like")
async def search_and_like(
    max_likes: int = Query(default=10, le=50),
    db: AsyncSession = Depends(get_db),
):
    result = await engagement_service.search_and_like(db, max_likes=max_likes)
    return result


@router.post("/engagement/reply-suggestion")
async def generate_reply_suggestion(
    req: ReplySuggestionRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await engagement_service.generate_reply_suggestion(
        tweet_text=req.tweet_text,
        tweet_id=req.tweet_id,
        db=db,
    )
    return result


@router.get("/engagement/stats")
async def get_engagement_stats(
    days: int = Query(default=7, le=30),
    db: AsyncSession = Depends(get_db),
):
    return await engagement_service.get_engagement_stats(db, days=days)


# --- Content Calendar ---

@router.get("/calendar")
async def get_content_calendar(
    days: int = Query(default=7, le=30),
):
    calendar = await gtm_service.get_content_calendar(days=days)
    return {"calendar": calendar}


# --- Reply Management ---

@router.post("/engagement/reply/{log_id}/approve")
async def approve_and_post_reply(
    log_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await engagement_service.post_approved_reply(log_id, db)
    if not result.get("success"):
        raise HTTPException(400, result.get("error", "Failed"))
    return result


@router.post("/engagement/reply/{log_id}/reject")
async def reject_reply(
    log_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await engagement_service.reject_reply(log_id, db)


# --- Prospect Pipeline ---

@router.get("/prospects")
async def list_prospects(
    stage: Optional[str] = None,
    min_score: int = 0,
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    prospects = await engagement_service.get_prospects(db, stage=stage, min_score=min_score, limit=limit)
    return {"prospects": prospects, "total": len(prospects)}


@router.get("/prospects/funnel")
async def prospect_funnel(
    db: AsyncSession = Depends(get_db),
):
    return await engagement_service.get_prospect_funnel(db)


class UpdateStageRequest(BaseModel):
    stage: str

@router.put("/prospects/{prospect_id}/stage")
async def update_prospect_stage(
    prospect_id: int,
    req: UpdateStageRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await engagement_service.update_prospect_stage(prospect_id, req.stage, db)
    if not result.get("success"):
        raise HTTPException(404, result.get("error", "Not found"))
    return result


@router.post("/prospects/discover")
async def discover_prospects(
    max_results: int = Query(default=20, le=50),
    db: AsyncSession = Depends(get_db),
):
    return await engagement_service.discover_prospects(db, max_results=max_results)


# --- Strategy Engine ---

@router.get("/strategy")
async def get_active_strategy(db: AsyncSession = Depends(get_db)):
    strat = await strategy_engine.get_active_strategy(db)
    if not strat:
        return {"active": False}
    return {"active": True, "strategy": strategy_engine._serialize_strategy(strat)}


@router.post("/strategy/create")
async def create_strategy(db: AsyncSession = Depends(get_db)):
    return await strategy_engine.create_strategy(db)


@router.post("/strategy/review")
async def review_strategy(db: AsyncSession = Depends(get_db)):
    return await strategy_engine.review_strategy(db)


@router.get("/strategy/kpis")
async def get_kpi_dashboard(db: AsyncSession = Depends(get_db)):
    return await strategy_engine.get_kpi_dashboard(db)


@router.get("/strategy/decisions")
async def get_decision_log(
    decision_type: Optional[str] = None,
    limit: int = Query(default=30, le=100),
    db: AsyncSession = Depends(get_db),
):
    logs = await strategy_engine.get_decision_log(db, limit=limit, decision_type=decision_type)
    return {"decisions": logs}


@router.get("/strategy/history")
async def get_strategy_history(
    limit: int = Query(default=10, le=50),
    db: AsyncSession = Depends(get_db),
):
    history = await strategy_engine.get_strategy_history(db, limit=limit)
    return {"strategies": history}


# --- Evaluation & Reports ---

@router.post("/evaluate")
async def run_gtm_evaluation(
    days: int = Query(default=7, le=30),
    db: AsyncSession = Depends(get_db),
):
    return await gtm_service.run_evaluation(db, days=days, report_type="manual")


@router.get("/reports")
async def get_gtm_reports(
    limit: int = Query(default=10, le=50),
    db: AsyncSession = Depends(get_db),
):
    reports = await gtm_service.get_reports(db, limit=limit)
    return {"reports": reports}


# --- Stats ---

@router.get("/stats")
async def get_marketing_stats(
    db: AsyncSession = Depends(get_db),
):
    gtm_stats = await gtm_service.get_stats(db)
    eng_stats = await engagement_service.get_engagement_stats(db)
    funnel = await engagement_service.get_prospect_funnel(db)
    return {**gtm_stats, "engagement": eng_stats, "prospect_funnel": funnel}
