from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from app.database import get_db
from app.models import RLEnvironment
from app.services.rl_service import rl_service

router = APIRouter(prefix="/api/rl-envs", tags=["RL Environments"])


@router.get("/")
async def list_environments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RLEnvironment).order_by(desc(RLEnvironment.created_at)))
    envs = result.scalars().all()
    return [
        {
            "id": e.id,
            "name": e.name,
            "description": e.description,
            "category": e.category,
            "observation_space": e.observation_space,
            "action_space": e.action_space,
            "reward_description": e.reward_description,
            "difficulty": e.difficulty,
            "status": e.status,
            "ai_model_used": e.ai_model_used,
            "topic": e.topic,
            "preview_image": e.preview_image,
            "published_at": e.published_at.isoformat() if e.published_at else None,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in envs
    ]


@router.post("/generate")
async def generate_environment(data: dict, db: AsyncSession = Depends(get_db)):
    """AI-generate an RL environment from a topic/description."""
    topic = data.get("topic", "").strip()
    category = data.get("category", "custom")
    difficulty = data.get("difficulty", "medium")
    if not topic:
        raise HTTPException(status_code=400, detail="Topic is required")

    result = await rl_service.generate_environment(topic, category, difficulty)

    env = RLEnvironment(
        name=result["name"],
        description=result["description"],
        category=category,
        observation_space=result.get("observation_space", ""),
        action_space=result.get("action_space", ""),
        reward_description=result.get("reward_description", ""),
        code=result.get("code", ""),
        difficulty=difficulty,
        status="draft",
        ai_model_used=result.get("model", "kimi-k2.5"),
        topic=topic,
    )
    db.add(env)
    await db.commit()
    await db.refresh(env)

    return {
        "id": env.id,
        "name": env.name,
        "description": env.description,
        "category": env.category,
        "status": "draft",
    }


@router.post("/create")
async def create_environment(data: dict, db: AsyncSession = Depends(get_db)):
    """Manually create an RL environment."""
    env = RLEnvironment(
        name=data.get("name", "Untitled Environment"),
        description=data.get("description"),
        category=data.get("category", "custom"),
        observation_space=data.get("observation_space"),
        action_space=data.get("action_space"),
        reward_description=data.get("reward_description"),
        code=data.get("code"),
        difficulty=data.get("difficulty", "medium"),
        status="draft",
        topic=data.get("topic"),
    )
    db.add(env)
    await db.commit()
    await db.refresh(env)
    return {"id": env.id, "name": env.name}


@router.put("/{env_id}")
async def update_environment(env_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RLEnvironment).where(RLEnvironment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    for field in ["name", "description", "category", "observation_space", "action_space", "reward_description", "code", "difficulty", "topic", "preview_image"]:
        if field in data:
            setattr(env, field, data[field])

    await db.commit()
    return {"success": True}


@router.post("/{env_id}/publish")
async def publish_environment(env_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RLEnvironment).where(RLEnvironment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    env.status = "published"
    env.published_at = datetime.utcnow()
    await db.commit()
    return {"success": True, "status": "published"}


@router.post("/{env_id}/unpublish")
async def unpublish_environment(env_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RLEnvironment).where(RLEnvironment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    env.status = "draft"
    env.published_at = None
    await db.commit()
    return {"success": True, "status": "draft"}


@router.delete("/{env_id}")
async def delete_environment(env_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RLEnvironment).where(RLEnvironment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    await db.delete(env)
    await db.commit()
    return {"success": True}
