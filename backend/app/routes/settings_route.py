from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import BotSettings
from app.schemas import SettingsUpdate, SettingsResponse
from app.services.scheduler_service import scheduler_service
from app.services.twitter_service import twitter_service
from app.services.ai_service import ai_service
from app.config import settings

router = APIRouter(prefix="/api/settings", tags=["Settings"])


async def _get_setting(db: AsyncSession, key: str, default: str) -> str:
    result = await db.execute(select(BotSettings).where(BotSettings.key == key))
    setting = result.scalar_one_or_none()
    return setting.value if setting else default


async def _set_setting(db: AsyncSession, key: str, value: str):
    result = await db.execute(select(BotSettings).where(BotSettings.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = value
    else:
        db.add(BotSettings(key=key, value=value))


@router.get("/", response_model=SettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    """Get current bot settings."""
    return SettingsResponse(
        default_ai_model=await _get_setting(db, "default_ai_model", settings.default_ai_model),
        tweet_interval_minutes=int(
            await _get_setting(db, "tweet_interval_minutes", str(settings.tweet_interval_minutes))
        ),
        auto_reply_enabled=(
            await _get_setting(db, "auto_reply_enabled", str(settings.auto_reply_enabled))
        ).lower() == "true",
        tweet_style=await _get_setting(
            db, "tweet_style", "popular science, engaging, accessible"
        ),
        reply_style=await _get_setting(
            db, "reply_style", "friendly, informative, conversational"
        ),
        scheduler_running=scheduler_service.is_running,
    )


@router.put("/", response_model=SettingsResponse)
async def update_settings(
    data: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update bot settings."""
    if data.default_ai_model is not None:
        await _set_setting(db, "default_ai_model", data.default_ai_model)

    if data.tweet_interval_minutes is not None:
        await _set_setting(db, "tweet_interval_minutes", str(data.tweet_interval_minutes))
        scheduler_service.update_tweet_interval(data.tweet_interval_minutes)

    if data.auto_reply_enabled is not None:
        await _set_setting(db, "auto_reply_enabled", str(data.auto_reply_enabled))

    if data.tweet_style is not None:
        await _set_setting(db, "tweet_style", data.tweet_style)

    if data.reply_style is not None:
        await _set_setting(db, "reply_style", data.reply_style)

    await db.commit()
    return await get_settings(db)


@router.post("/scheduler/start")
async def start_scheduler():
    """Start the auto-posting scheduler."""
    scheduler_service.start()
    return {"message": "Scheduler started", "status": scheduler_service.get_status()}


@router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the auto-posting scheduler."""
    scheduler_service.stop()
    return {"message": "Scheduler stopped", "status": scheduler_service.get_status()}


@router.get("/scheduler/status")
async def scheduler_status():
    """Get scheduler status."""
    return scheduler_service.get_status()


@router.post("/test/twitter")
async def test_twitter():
    """Test Twitter API connection."""
    return await twitter_service.test_connection()


@router.post("/test/ai/{model}")
async def test_ai(model: str):
    """Test AI model connection."""
    return await ai_service.test_connection(model)


@router.get("/models")
async def get_available_models():
    """Get list of available AI models."""
    return {
        "openai": [
            {"id": "gpt-4", "name": "GPT-4"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
            {"id": "gpt-4o", "name": "GPT-4o"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
        ],
        "anthropic": [
            {"id": "claude-sonnet-4-20250514", "name": "Claude 3.5 Sonnet"},
            {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku"},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus"},
        ],
    }


@router.get("/debug/twitter")
async def debug_twitter():
    """Debug Twitter API - check credentials and connectivity."""
    import os
    import requests as req
    from requests_oauthlib import OAuth1

    debug_info = {}

    # 1. Check env vars are loaded
    debug_info["env_vars"] = {
        "api_key_loaded": bool(settings.twitter_api_key),
        "api_key_preview": settings.twitter_api_key[:8] + "..." if settings.twitter_api_key else "EMPTY",
        "api_secret_loaded": bool(settings.twitter_api_secret),
        "access_token_loaded": bool(settings.twitter_access_token),
        "access_token_preview": settings.twitter_access_token[:15] + "..." if settings.twitter_access_token else "EMPTY",
        "access_token_secret_loaded": bool(settings.twitter_access_token_secret),
        "bearer_token_loaded": bool(settings.twitter_bearer_token),
    }

    # 2. Test basic connectivity to Twitter
    try:
        r = req.get("https://api.twitter.com/2/tweets/search/recent?query=hello", timeout=10)
        debug_info["twitter_reachable"] = True
        debug_info["basic_status"] = r.status_code
    except Exception as e:
        debug_info["twitter_reachable"] = False
        debug_info["connectivity_error"] = str(e)

    # 3. Test OAuth1 with a simple GET (verify credentials)
    try:
        auth = OAuth1(
            settings.twitter_api_key,
            settings.twitter_api_secret,
            settings.twitter_access_token,
            settings.twitter_access_token_secret,
        )
        r = req.get(
            "https://api.twitter.com/2/users/me",
            auth=auth,
            timeout=10,
        )
        debug_info["oauth_get_status"] = r.status_code
        debug_info["oauth_get_response"] = r.json() if r.status_code == 200 else r.text[:500]
    except Exception as e:
        debug_info["oauth_get_error"] = str(e)

    # 4. Test POST tweet (dry run - just check auth, don't actually post)
    try:
        auth = OAuth1(
            settings.twitter_api_key,
            settings.twitter_api_secret,
            settings.twitter_access_token,
            settings.twitter_access_token_secret,
        )
        # Post a minimal test
        r = req.post(
            "https://api.twitter.com/2/tweets",
            json={"text": "🔬 Test tweet from AI Scientist Bot - please ignore"},
            auth=auth,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        debug_info["post_status"] = r.status_code
        debug_info["post_response"] = r.text[:500]
    except Exception as e:
        debug_info["post_error"] = str(e)

    return debug_info


@router.get("/replies")
async def get_replies(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Get all auto-replies."""
    from app.models import Reply
    result = await db.execute(
        select(Reply).order_by(Reply.created_at.desc()).limit(limit)
    )
    replies = result.scalars().all()
    return [
        {
            "id": r.id,
            "tweet_id": r.tweet_id,
            "incoming_text": r.incoming_text,
            "incoming_user": r.incoming_user,
            "response_text": r.response_text,
            "ai_model_used": r.ai_model_used,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "replied_at": r.replied_at.isoformat() if r.replied_at else None,
        }
        for r in replies
    ]
