from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Tweet, Reply, Article, ActivityLog
from app.schemas import DashboardStats, ActivityLogResponse

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics."""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Total counts
    total_tweets = (await db.execute(select(func.count(Tweet.id)))).scalar() or 0
    total_replies = (await db.execute(select(func.count(Reply.id)))).scalar() or 0
    total_articles = (await db.execute(select(func.count(Article.id)))).scalar() or 0

    # Engagement totals
    total_likes = (await db.execute(select(func.sum(Tweet.likes)))).scalar() or 0
    total_retweets = (await db.execute(select(func.sum(Tweet.retweets)))).scalar() or 0
    total_impressions = (await db.execute(select(func.sum(Tweet.impressions)))).scalar() or 0

    # Today counts
    tweets_today = (
        await db.execute(
            select(func.count(Tweet.id)).where(Tweet.posted_at >= today)
        )
    ).scalar() or 0

    replies_today = (
        await db.execute(
            select(func.count(Reply.id)).where(Reply.replied_at >= today)
        )
    ).scalar() or 0

    # Average engagement rate
    avg_engagement = 0.0
    if total_impressions > 0 and total_tweets > 0:
        total_engagement = total_likes + total_retweets + total_replies
        avg_engagement = round((total_engagement / total_impressions) * 100, 2)

    return DashboardStats(
        total_tweets=total_tweets,
        total_replies=total_replies,
        total_articles=total_articles,
        total_likes=total_likes,
        total_retweets=total_retweets,
        total_impressions=total_impressions,
        tweets_today=tweets_today,
        replies_today=replies_today,
        avg_engagement_rate=avg_engagement,
    )


@router.get("/activity", response_model=list[ActivityLogResponse])
async def get_activity_logs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Get recent activity logs."""
    result = await db.execute(
        select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit)
    )
    return result.scalars().all()


@router.get("/chart-data")
async def get_chart_data(days: int = 7, db: AsyncSession = Depends(get_db)):
    """Get tweet/engagement data for charts."""
    start_date = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(Tweet).where(
            Tweet.posted_at >= start_date,
            Tweet.status == "posted",
        ).order_by(Tweet.posted_at.asc())
    )
    tweets = result.scalars().all()

    chart_data = []
    for tweet in tweets:
        chart_data.append({
            "date": tweet.posted_at.strftime("%Y-%m-%d %H:%M") if tweet.posted_at else "",
            "likes": tweet.likes,
            "retweets": tweet.retweets,
            "replies": tweet.replies_count,
            "impressions": tweet.impressions,
        })

    return chart_data
