import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from app.config import settings
from app.database import get_db
from app.models import RLEnvironment
from app.services.architect_service import architect_service
from app.services.sandbox_runner import sandbox_runner
from app.auth import require_admin

logger = logging.getLogger("rl_envs")

router = APIRouter(prefix="/api/rl-envs", tags=["RL Environments"], dependencies=[Depends(require_admin)])


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
    """AI-generate an RL environment using architect_service + sandbox tests + fix loop."""
    topic = data.get("topic", "").strip()
    category = data.get("category", "custom")
    difficulty = data.get("difficulty", "medium")
    if not topic:
        raise HTTPException(status_code=400, detail="Topic is required")

    log_lines = [f"[start] Generating env: {topic[:100]}..."]

    gen = await architect_service.generate_env_code(topic, domain=category, difficulty=difficulty)
    code = gen.get("code", "")
    spec_json = json.dumps(gen.get("env_spec", {}))
    log_lines.append(f"[code] Generated {len(code)} chars of code")

    test_results = await sandbox_runner.run_all_tests(code)
    code, test_results, fix_log = await architect_service.auto_fix_until_passing(
        code, spec_json, test_results, max_attempts=4,
    )
    log_lines.extend(f"[fix] {line}" for line in fix_log)

    # Quality gate: only publish environments that pass the threshold.
    auto_publish = data.get("auto_publish", True) and test_results.get("passed", 0) >= architect_service.PASS_THRESHOLD
    status = "published" if auto_publish else "draft"
    if data.get("auto_publish", True) and not auto_publish:
        log_lines.append(f"[gate] Not published: only {test_results.get('passed', 0)}/{test_results.get('total', 0)} tests pass (need {architect_service.PASS_THRESHOLD}+). Saved as draft.")

    env = RLEnvironment(
        name=gen.get("name", topic[:100]),
        description=gen.get("description", topic),
        category=category,
        observation_space=gen.get("observation_space", ""),
        action_space=gen.get("action_space", ""),
        reward_description=gen.get("reward_description", ""),
        code=code,
        difficulty=difficulty,
        status=status,
        ai_model_used=settings.anthropic_model,
        topic=topic,
        published_at=datetime.utcnow() if auto_publish else None,
    )
    db.add(env)
    await db.commit()
    await db.refresh(env)

    logger.info("Generated env %d (%s): %s/%s tests passed",
                env.id, env.name, test_results["passed"], test_results["total"])

    return {
        "id": env.id,
        "name": env.name,
        "description": env.description,
        "category": env.category,
        "status": env.status,
        "tests_passed": test_results["passed"],
        "tests_total": test_results["total"],
        "generation_log": "\n".join(log_lines),
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

    from sqlalchemy import delete as sql_delete
    from app.models import TrainingRun, EnvVersion
    await db.execute(sql_delete(TrainingRun).where(TrainingRun.env_id == env_id))
    await db.execute(sql_delete(EnvVersion).where(EnvVersion.env_id == env_id))
    await db.delete(env)
    await db.commit()
    return {"success": True}
