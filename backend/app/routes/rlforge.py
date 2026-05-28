import json
import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_
from app.rate_limit import limiter

from app.config import settings
from app.database import get_db
from app.models import (
    RLEnvironment, BuilderConversation, TrainingRun,
    EnvVersion, SkillCache, User,
)
from app.auth import get_optional_user, get_current_user
from app.services.architect_service import architect_service
from app.services.sandbox_runner import sandbox_runner
from app.services.training_service import training_service
from app.services.session_manager import session_manager
from app.services.paper_parser import paper_parser
from app.services.credit_service import credit_service, UsageAccumulator, CreditService

logger = logging.getLogger("rlforge_api")

router = APIRouter(prefix="/api/rlforge", tags=["RLForge"])


async def _resolve_user_id(db: AsyncSession, auth_user: Optional[dict]) -> Optional[int]:
    """Resolve Clerk user to internal user_id. Returns None if no auth."""
    if not auth_user:
        return None
    clerk_id = auth_user.get("clerk_user_id")
    if not clerk_id:
        return None
    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = result.scalar_one_or_none()
    return user.id if user else None


def _slugify(text: str) -> str:
    import re
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:200] if slug else "env"


def _env_to_dict(e: RLEnvironment, include_code: bool = False) -> dict:
    d = {
        "id": e.id,
        "name": e.name,
        "slug": e.slug,
        "description": e.description,
        "category": e.category,
        "domain": e.domain,
        "observation_space": e.observation_space,
        "action_space": e.action_space,
        "reward_description": e.reward_description,
        "difficulty": e.difficulty,
        "status": e.status,
        "version": e.version,
        "max_steps": e.max_steps,
        "is_template": e.is_template,
        "ai_model_used": e.ai_model_used,
        "topic": e.topic,
        "test_results": json.loads(e.test_results_json) if e.test_results_json else None,
        "published_at": e.published_at.isoformat() if e.published_at else None,
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "updated_at": e.updated_at.isoformat() if e.updated_at else None,
    }
    if include_code:
        d["code"] = e.code
        d["env_spec"] = json.loads(e.env_spec_json) if e.env_spec_json else None
        d["generation_log"] = e.generation_log
    return d


# ──────────────────────────────────────────────────
#  CATALOG
# ──────────────────────────────────────────────────

@router.get("/catalog")
async def list_catalog(
    domain: Optional[str] = None,
    difficulty: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(RLEnvironment).where(RLEnvironment.status == "published")
    if domain:
        query = query.where(RLEnvironment.domain == domain)
    if difficulty:
        query = query.where(RLEnvironment.difficulty == difficulty)
    if search:
        query = query.where(
            or_(
                RLEnvironment.name.ilike(f"%{search}%"),
                RLEnvironment.description.ilike(f"%{search}%"),
            )
        )
    query = query.order_by(desc(RLEnvironment.published_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    envs = result.scalars().all()

    count_q = select(func.count()).select_from(RLEnvironment).where(RLEnvironment.status == "published")
    if domain:
        count_q = count_q.where(RLEnvironment.domain == domain)
    if difficulty:
        count_q = count_q.where(RLEnvironment.difficulty == difficulty)
    total = (await db.execute(count_q)).scalar()

    return {"items": [_env_to_dict(e) for e in envs], "total": total}


@router.get("/catalog/{slug}")
async def get_catalog_env(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RLEnvironment).where(
            RLEnvironment.slug == slug,
            RLEnvironment.status == "published",
        )
    )
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(404, "Environment not found")
    return _env_to_dict(env, include_code=True)


@router.get("/templates")
async def list_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RLEnvironment)
        .where(RLEnvironment.is_template == True)
        .order_by(RLEnvironment.domain, RLEnvironment.difficulty)
    )
    return [_env_to_dict(e, include_code=True) for e in result.scalars().all()]


# ──────────────────────────────────────────────────
#  GENERATE
# ──────────────────────────────────────────────────

@router.post("/generate")
@limiter.limit("5/minute")
async def generate_env(
    request: Request,
    data: dict,
    db: AsyncSession = Depends(get_db),
    auth_user: Optional[dict] = Depends(get_optional_user),
):
    description = data.get("description", "").strip()
    domain = data.get("domain")
    difficulty = data.get("difficulty", "medium")
    if not description:
        raise HTTPException(400, "description is required")

    user_id = await _resolve_user_id(db, auth_user)

    # Credit & plan check for authenticated users
    if user_id:
        est = credit_service.estimate_operation_cost("env_generation")
        check = await credit_service.check_credits(user_id, est, db)
        if not check["ok"]:
            raise HTTPException(402, detail={
                "error": "insufficient_credits",
                "balance": check["balance"],
                "required": check["required"],
                "message": f"Not enough credits. You need ~${est:.2f} but have ${check['balance']:.2f}.",
            })
        plan_check = await credit_service.check_plan_limit(user_id, "environments", db)
        if not plan_check["ok"]:
            raise HTTPException(403, detail={
                "error": "plan_limit_reached",
                "limit": plan_check.get("limit"),
                "current": plan_check.get("current"),
                "message": "Environment limit reached for your plan. Please upgrade.",
            })

    usage_acc = UsageAccumulator()

    log_lines = []
    log_lines.append(f"[start] Generating env: {description[:100]}...")

    gen = await architect_service.generate_env_code(description, domain=domain, difficulty=difficulty, usage_acc=usage_acc)
    code = gen.get("code", "")
    spec_json = json.dumps(gen.get("env_spec", {}))
    log_lines.append(f"[code] Generated {len(code)} chars of code")

    test_results = await sandbox_runner.run_all_tests(code)
    log_lines.append(f"[test] {test_results['passed']}/{test_results['total']} passed")

    max_fix_attempts = 3 if test_results["passed"] < 6 else 2
    attempts = 0
    while test_results["failed"] > 0 and attempts < max_fix_attempts:
        attempts += 1
        log_lines.append(f"[fix] Attempt {attempts}: fixing {test_results['failed']} failed tests")
        fixed_code = await architect_service.fix_env_code(code, spec_json, json.dumps(test_results), usage_acc=usage_acc)
        if fixed_code and fixed_code != code:
            code = fixed_code
            test_results = await sandbox_runner.run_all_tests(code)
            log_lines.append(f"[test] {test_results['passed']}/{test_results['total']} passed after fix {attempts}")
        else:
            log_lines.append(f"[fix] No change from fix attempt {attempts}")
            break

    detected_domain = gen.get("domain") or (domain if domain else "custom")
    slug_base = _slugify(gen.get("name", description[:50]))

    existing = await db.execute(select(RLEnvironment).where(RLEnvironment.slug == slug_base))
    if existing.scalar_one_or_none():
        slug_base = f"{slug_base}-{int(datetime.utcnow().timestamp())}"

    env = RLEnvironment(
        name=gen.get("name", description[:100]),
        slug=slug_base,
        description=gen.get("description", description),
        category=gen.get("category", "custom"),
        domain=detected_domain,
        observation_space=gen.get("observation_space", ""),
        action_space=gen.get("action_space", ""),
        reward_description=gen.get("reward_description", ""),
        code=code,
        env_spec_json=spec_json,
        test_results_json=json.dumps(test_results),
        difficulty=difficulty,
        status="draft",
        ai_model_used=settings.anthropic_model,
        topic=description,
        generation_log="\n".join(log_lines),
        max_steps=gen.get("env_spec", {}).get("max_episode_steps", 1000),
        user_id=user_id,
    )
    db.add(env)
    await db.commit()
    await db.refresh(env)

    version = EnvVersion(
        env_id=env.id,
        version=1,
        code=code,
        spec_json=spec_json,
        change_summary="Initial generation",
    )
    db.add(version)
    await db.commit()

    # Deduct credits based on actual LLM usage
    billed = usage_acc.billed_cost()
    if user_id and billed > 0:
        await credit_service.consume_credits(
            user_id, billed, "env_generation", db,
            resource_id=env.id, details=usage_acc.to_dict(),
        )

    # Email notification: env ready
    if user_id:
        try:
            from app.services.email_service import email_service
            user_obj = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
            if user_obj and user_obj.email and user_obj.email_notifications:
                await email_service.send_transactional(
                    to=user_obj.email, template="env_ready",
                    data={
                        "env_name": env.name,
                        "env_id": env.id,
                        "tests_passed": test_results.get("passed", 0),
                        "tests_total": test_results.get("total", 8),
                        "domain": env.domain or "general",
                        "difficulty": env.difficulty or "medium",
                    },
                    user_id=user_id,
                )
        except Exception:
            pass

    return {
        "id": env.id,
        "slug": env.slug,
        "name": env.name,
        "test_results": test_results,
        "generation_log": "\n".join(log_lines),
        "credits_used": round(billed, 4),
    }


@router.get("/envs/{env_id}")
async def get_env_detail(env_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RLEnvironment).where(RLEnvironment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(404, "Environment not found")
    return _env_to_dict(env, include_code=True)


@router.post("/fork/{env_id}")
async def fork_env(
    env_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    auth_user: Optional[dict] = Depends(get_optional_user),
):
    result = await db.execute(select(RLEnvironment).where(RLEnvironment.id == env_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(404, "Source environment not found")

    modifications = data.get("modifications", "")
    if modifications:
        iterated = await architect_service.iterate_env(
            source.code or "",
            source.env_spec_json or "{}",
            modifications,
        )
        code = iterated.get("updated_code", source.code)
        spec_json = json.dumps(iterated.get("updated_spec", {}))
        summary = iterated.get("change_summary", "Forked")
    else:
        code = source.code
        spec_json = source.env_spec_json
        summary = "Direct fork"

    slug = _slugify(f"{source.name}-fork")
    existing = await db.execute(select(RLEnvironment).where(RLEnvironment.slug == slug))
    if existing.scalar_one_or_none():
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

    test_results = await sandbox_runner.run_all_tests(code) if code else {"passed": 0, "failed": 8, "total": 8, "tests": []}

    fork_user_id = await _resolve_user_id(db, auth_user)

    forked = RLEnvironment(
        name=f"{source.name} (fork)",
        slug=slug,
        description=source.description,
        category=source.category,
        domain=source.domain,
        observation_space=source.observation_space,
        action_space=source.action_space,
        reward_description=source.reward_description,
        code=code,
        env_spec_json=spec_json,
        test_results_json=json.dumps(test_results),
        difficulty=source.difficulty,
        status="draft",
        ai_model_used=source.ai_model_used,
        topic=f"Fork of {source.name}: {modifications}" if modifications else f"Fork of {source.name}",
        generation_log=summary,
        max_steps=source.max_steps,
        user_id=fork_user_id,
    )
    db.add(forked)
    await db.commit()
    await db.refresh(forked)

    v = EnvVersion(env_id=forked.id, version=1, code=code, spec_json=spec_json, change_summary=summary)
    db.add(v)
    await db.commit()

    return {"id": forked.id, "slug": forked.slug, "name": forked.name, "test_results": test_results}


# ──────────────────────────────────────────────────
#  BUILDER (Chat-based iteration)
# ──────────────────────────────────────────────────

@router.post("/builder/{env_id}/chat")
@limiter.limit("20/minute")
async def builder_chat(request: Request, env_id: int, data: dict, db: AsyncSession = Depends(get_db), auth_user: Optional[dict] = Depends(get_optional_user)):
    result = await db.execute(select(RLEnvironment).where(RLEnvironment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(404, "Environment not found")

    message = data.get("message", "").strip()
    if not message:
        raise HTTPException(400, "message is required")

    user_id = await _resolve_user_id(db, auth_user)
    if user_id:
        est = credit_service.estimate_operation_cost("builder_chat")
        check = await credit_service.check_credits(user_id, est, db)
        if not check["ok"]:
            raise HTTPException(402, detail={
                "error": "insufficient_credits",
                "balance": check["balance"],
                "required": check["required"],
                "message": f"Not enough credits for this operation.",
            })

    user_msg = BuilderConversation(
        env_id=env_id, role="user", content=message, version_snapshot=env.version
    )
    db.add(user_msg)

    # Gather project context: latest training run, replay, history
    project_context: dict = {}
    try:
        latest_run_res = await db.execute(
            select(TrainingRun)
            .where(TrainingRun.env_id == env_id)
            .order_by(desc(TrainingRun.id))
            .limit(1)
        )
        latest_run = latest_run_res.scalar_one_or_none()
        if latest_run:
            run_data: dict = {
                "id": latest_run.id,
                "algorithm": latest_run.algorithm,
                "status": latest_run.status,
                "total_timesteps": None,
            }
            if latest_run.config_json:
                try:
                    cfg = json.loads(latest_run.config_json)
                    run_data["total_timesteps"] = cfg.get("total_timesteps")
                except json.JSONDecodeError:
                    pass
            if latest_run.results_json:
                try:
                    run_data["results"] = json.loads(latest_run.results_json)
                except json.JSONDecodeError:
                    pass
            project_context["latest_training"] = run_data

            # Load replay data from disk
            replay_path = os.path.join(
                training_service.MODELS_DIR, f"run_{latest_run.id}", "replay.json"
            )
            if os.path.exists(replay_path):
                try:
                    with open(replay_path) as f:
                        project_context["replay"] = json.load(f)
                except (json.JSONDecodeError, IOError):
                    pass

        # Training history (all runs for this env)
        hist_res = await db.execute(
            select(TrainingRun)
            .where(TrainingRun.env_id == env_id)
            .order_by(desc(TrainingRun.id))
            .limit(10)
        )
        hist_runs = hist_res.scalars().all()
        if hist_runs:
            history_list = []
            for hr in hist_runs:
                h: dict = {
                    "id": hr.id,
                    "algorithm": hr.algorithm,
                    "status": hr.status,
                }
                if hr.config_json:
                    try:
                        c = json.loads(hr.config_json)
                        h["total_timesteps"] = c.get("total_timesteps")
                        h["env_version"] = c.get("env_version")
                    except json.JSONDecodeError:
                        pass
                if hr.results_json:
                    try:
                        r = json.loads(hr.results_json)
                        h["mean_reward"] = r.get("mean_reward")
                        h["success_rate"] = r.get("success_rate")
                    except json.JSONDecodeError:
                        pass
                history_list.append(h)
            project_context["history"] = history_list
    except Exception as e:
        logger.warning("Failed to gather project context for chat: %s", e)

    chat_usage = UsageAccumulator()
    iterated = await architect_service.iterate_env(
        env.code or "",
        env.env_spec_json or "{}",
        message,
        project_context=project_context,
        usage_acc=chat_usage,
    )

    mode = iterated.get("mode", "change")
    change_summary = iterated.get("change_summary", "Updated")
    breaking = iterated.get("breaking_changes", [])

    if mode == "question":
        assistant_msg = BuilderConversation(
            env_id=env_id,
            role="assistant",
            content=json.dumps({
                "mode": "question",
                "change_summary": change_summary,
                "breaking_changes": [],
                "test_results": None,
            }),
            version_snapshot=env.version,
        )
        db.add(assistant_msg)
        await db.commit()
        return {
            "mode": "question",
            "version": env.version,
            "change_summary": change_summary,
            "breaking_changes": [],
            "test_results": None,
            "code": env.code,
        }

    new_code = iterated.get("updated_code", env.code)
    new_spec = iterated.get("updated_spec", {})

    test_results = await sandbox_runner.run_all_tests(new_code)

    env.version += 1
    env.code = new_code
    env.env_spec_json = json.dumps(new_spec) if isinstance(new_spec, dict) else new_spec
    env.test_results_json = json.dumps(test_results)
    if new_spec.get("name"):
        env.name = new_spec["name"]
    if new_spec.get("observation_space"):
        env.observation_space = str(new_spec["observation_space"])
    if new_spec.get("action_space"):
        env.action_space = str(new_spec["action_space"])
    if new_spec.get("reward_function"):
        env.reward_description = str(new_spec["reward_function"])

    assistant_msg = BuilderConversation(
        env_id=env_id,
        role="assistant",
        content=json.dumps({
            "mode": "change",
            "change_summary": change_summary,
            "breaking_changes": breaking,
            "test_results": test_results,
        }),
        version_snapshot=env.version,
    )
    db.add(assistant_msg)

    ver = EnvVersion(
        env_id=env_id, version=env.version, code=new_code,
        spec_json=env.env_spec_json, change_summary=change_summary,
    )
    db.add(ver)
    await db.commit()

    billed = chat_usage.billed_cost()
    if user_id and billed > 0:
        await credit_service.consume_credits(
            user_id, billed, "builder_chat", db,
            resource_id=env_id, details=chat_usage.to_dict(),
        )

    return {
        "mode": "change",
        "version": env.version,
        "change_summary": change_summary,
        "breaking_changes": breaking,
        "test_results": test_results,
        "code": new_code,
        "credits_used": round(billed, 4),
    }


@router.get("/builder/{env_id}/history")
async def builder_history(env_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BuilderConversation)
        .where(BuilderConversation.env_id == env_id)
        .order_by(BuilderConversation.created_at)
    )
    msgs = result.scalars().all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "version_snapshot": m.version_snapshot,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in msgs
    ]


@router.post("/builder/{env_id}/rollback")
async def builder_rollback(env_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    target_version = data.get("version")
    if not target_version:
        raise HTTPException(400, "version is required")

    result = await db.execute(select(RLEnvironment).where(RLEnvironment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(404, "Environment not found")

    ver_result = await db.execute(
        select(EnvVersion).where(EnvVersion.env_id == env_id, EnvVersion.version == target_version)
    )
    ver = ver_result.scalar_one_or_none()
    if not ver:
        raise HTTPException(404, f"Version {target_version} not found")

    env.code = ver.code
    env.env_spec_json = ver.spec_json
    env.version = target_version

    test_results = await sandbox_runner.run_all_tests(ver.code) if ver.code else {"passed": 0, "failed": 8, "total": 8, "tests": []}
    env.test_results_json = json.dumps(test_results)

    rollback_msg = BuilderConversation(
        env_id=env_id, role="system",
        content=f"Rolled back to version {target_version}",
        version_snapshot=target_version,
    )
    db.add(rollback_msg)
    await db.commit()

    return {"version": target_version, "test_results": test_results}


@router.post("/builder/{env_id}/export-zip")
async def export_zip(env_id: int, db: AsyncSession = Depends(get_db)):
    import io
    import zipfile
    from fastapi.responses import StreamingResponse

    result = await db.execute(select(RLEnvironment).where(RLEnvironment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(404, "Environment not found")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        env_name = _slugify(env.name) or "environment"
        zf.writestr(f"{env_name}/env.py", env.code or "# No code generated yet")
        zf.writestr(f"{env_name}/env_config.json", env.env_spec_json or "{}")

        readme = f"# {env.name}\n\n{env.description or ''}\n\n## Usage\n\n```python\nimport gymnasium as gym\nfrom env import *\n\nenv = gym.make('{env_name}')\nobs, info = env.reset()\n```\n"
        zf.writestr(f"{env_name}/README.md", readme)
        zf.writestr(f"{env_name}/requirements.txt", "gymnasium>=0.29.0\nnumpy>=1.24.0\n")

        test_script = f"""from env import *
import gymnasium as gym
import numpy as np

# Find env class
import inspect, sys
env_cls = None
for name, obj in inspect.getmembers(sys.modules['env']):
    if inspect.isclass(obj) and issubclass(obj, gym.Env) and obj is not gym.Env:
        env_cls = obj
        break

assert env_cls, "No Env class found"
env = env_cls()
obs, info = env.reset(seed=42)
print(f"Observation shape: {{obs.shape}}")
for i in range(10):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"Step {{i+1}}: reward={{reward:.3f}}, done={{terminated or truncated}}")
    if terminated or truncated:
        obs, info = env.reset()
env.close()
print("All tests passed!")
"""
        zf.writestr(f"{env_name}/examples/test_env.py", test_script)

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={_slugify(env.name)}.zip"},
    )


@router.post("/builder/{env_id}/export-github")
async def export_github(env_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    raise HTTPException(501, "GitHub export requires a GitHub token. Coming soon.")


# ──────────────────────────────────────────────────
#  ENV VERSIONS
# ──────────────────────────────────────────────────

@router.get("/envs/{env_id}/versions")
async def list_versions(env_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EnvVersion).where(EnvVersion.env_id == env_id).order_by(desc(EnvVersion.version))
    )
    versions = result.scalars().all()
    return [
        {
            "id": v.id,
            "version": v.version,
            "change_summary": v.change_summary,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]


# ──────────────────────────────────────────────────
#  TRAINING (SB3)
# ──────────────────────────────────────────────────

@router.post("/train/{env_id}")
@limiter.limit("10/minute")
async def start_training(request: Request, env_id: int, data: dict = None, db: AsyncSession = Depends(get_db), auth_user: Optional[dict] = Depends(get_optional_user)):
    data = data or {}

    result = await db.execute(select(RLEnvironment).where(RLEnvironment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(404, "Environment not found")

    user_id = await _resolve_user_id(db, auth_user)
    total_timesteps = data.get("total_timesteps", 10000)

    if user_id:
        training_cost = CreditService.calculate_training_cost(total_timesteps)
        check = await credit_service.check_credits(user_id, training_cost, db)
        if not check["ok"]:
            raise HTTPException(402, detail={
                "error": "insufficient_credits",
                "balance": check["balance"],
                "required": check["required"],
                "message": f"Training {total_timesteps:,} steps costs ${training_cost:.2f}. You have ${check['balance']:.2f}.",
            })
        plan_check = await credit_service.check_plan_limit(user_id, "training_steps", db)
        if total_timesteps > plan_check.get("max_steps", 50000):
            raise HTTPException(403, detail={
                "error": "plan_limit_exceeded",
                "max_steps": plan_check.get("max_steps"),
                "requested": total_timesteps,
                "message": f"Your plan allows max {plan_check.get('max_steps'):,} steps per run.",
            })

    is_curriculum = data.get("curriculum", False)
    if is_curriculum:
        last_run_result = await db.execute(
            select(TrainingRun).where(
                TrainingRun.env_id == env_id, TrainingRun.status == "completed"
            ).order_by(desc(TrainingRun.created_at)).limit(1)
        )
        last_run = last_run_result.scalar_one_or_none()
        results_summary = ""
        if last_run and last_run.results_json:
            r = json.loads(last_run.results_json)
            results_summary = (
                f"Last training: {last_run.algorithm}, mean_reward={r.get('mean_reward')}, "
                f"success_rate={r.get('success_rate')}, ep_length={r.get('mean_ep_length')}"
            )

        curriculum_msg = (
            f"Increase the difficulty of this environment for curriculum learning. "
            f"The agent has already been trained and achieved these results: {results_summary}. "
            f"Make it harder: increase obstacles, reduce time limits, make rewards sparser, "
            f"add complexity, increase stochasticity, or tighten success criteria. "
            f"The observation and action spaces MUST remain the same shape and type "
            f"so the trained model can continue learning."
        )
        try:
            spec_json = env.env_spec_json or "{}"
            updated = await architect_service.iterate_env(env.code, spec_json, curriculum_msg)
            new_code = updated.get("updated_code", env.code)
            new_spec = updated.get("updated_spec", spec_json)
            if isinstance(new_spec, dict):
                new_spec = json.dumps(new_spec)

            test_results = await sandbox_runner.run_all_tests(new_code)
            if test_results["passed"] >= 5:
                env.version = (env.version or 1) + 1
                env.code = new_code
                env.env_spec_json = new_spec
                new_version = EnvVersion(
                    env_id=env_id, version=env.version,
                    code=new_code, spec_json=new_spec,
                    change_summary=f"Curriculum: difficulty increased ({test_results['passed']}/{test_results['total']} tests)",
                )
                db.add(new_version)
                await db.commit()
                logger.info("Curriculum: env %d upgraded to v%d", env_id, env.version)
        except Exception as e:
            logger.warning("Curriculum iteration failed, training on current env: %s", e)

    env_version = env.version if env else 1

    config = {
        "total_timesteps": data.get("total_timesteps", 10000),
        "algorithm": data.get("algorithm"),
        "learning_rate": data.get("learning_rate"),
        "n_eval_episodes": data.get("n_eval_episodes", 5),
        "env_version": env_version,
        "batch_size": data.get("batch_size"),
        "gamma": data.get("gamma"),
        "net_arch": data.get("net_arch"),
    }
    if data.get("continue_from"):
        config["continue_from"] = True

    try:
        run = await training_service.start_training(env_id, config, db)

        # Deduct training credits
        if user_id:
            training_cost = CreditService.calculate_training_cost(config["total_timesteps"])
            await credit_service.consume_credits(
                user_id, training_cost, "training", db,
                resource_id=run.id,
                details={"env_id": env_id, "algorithm": run.algorithm, "timesteps": config["total_timesteps"]},
            )

        return {
            "run_id": run.id,
            "env_id": run.env_id,
            "algorithm": run.algorithm,
            "status": run.status,
            "total_timesteps": config["total_timesteps"],
            "config": json.loads(run.config_json) if run.config_json else config,
            "curriculum_applied": is_curriculum,
            "credits_used": round(CreditService.calculate_training_cost(config["total_timesteps"]), 4) if user_id else 0,
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error("Training start failed: %s", e)
        raise HTTPException(500, f"Training failed: {e}")


@router.get("/train/{env_id}/history")
async def training_history(env_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TrainingRun)
        .where(TrainingRun.env_id == env_id)
        .order_by(desc(TrainingRun.created_at))
    )
    runs = result.scalars().all()
    out = []
    for r in runs:
        cfg = json.loads(r.config_json) if r.config_json else {}
        res = json.loads(r.results_json) if r.results_json else None
        started = r.started_at
        completed = r.completed_at
        duration = None
        if started and completed:
            duration = round((completed - started).total_seconds(), 1)
        out.append({
            "id": r.id,
            "algorithm": r.algorithm,
            "status": r.status,
            "config": cfg,
            "env_version": cfg.get("env_version", "?"),
            "total_timesteps": cfg.get("total_timesteps", "?"),
            "results": res,
            "mean_reward": res.get("mean_reward") if res else None,
            "success_rate": res.get("success_rate") if res else None,
            "training_time_sec": res.get("training_time_sec") if res else duration,
            "started_at": started.isoformat() if started else None,
            "completed_at": completed.isoformat() if completed else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return out


@router.get("/train/{env_id}/report/{run_id}")
async def training_report(env_id: int, run_id: int, db: AsyncSession = Depends(get_db)):
    """Full training report for a specific run."""
    result = await db.execute(
        select(TrainingRun).where(TrainingRun.id == run_id, TrainingRun.env_id == env_id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(404, "Training run not found")

    env_result = await db.execute(select(RLEnvironment).where(RLEnvironment.id == env_id))
    env = env_result.scalar_one_or_none()

    cfg = json.loads(run.config_json) if run.config_json else {}
    res = json.loads(run.results_json) if run.results_json else {}
    curve = json.loads(run.training_curve_json) if run.training_curve_json else []

    if not curve:
        output_dir = os.path.abspath(os.path.join(
            os.getenv("DATA_DIR", "./data"), "trained_models", f"run_{run.id}"
        ))
        curve_path = os.path.join(output_dir, "curve.json")
        if os.path.exists(curve_path):
            try:
                with open(curve_path) as f:
                    curve = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

    return {
        "run_id": run.id,
        "env_id": env_id,
        "env_name": env.name if env else "Unknown",
        "env_version": cfg.get("env_version", "?"),
        "algorithm": run.algorithm,
        "status": run.status,
        "config": cfg,
        "results": res,
        "curve": curve,
        "hyperparameters": res.get("hyperparameters", {}),
        "reproducibility": {
            "random_seed": res.get("random_seed"),
            "sb3_version": res.get("sb3_version", "unknown"),
            "gymnasium_version": res.get("gymnasium_version", "unknown"),
            "env_version": cfg.get("env_version", "?"),
        },
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


@router.get("/train/{env_id}/status")
async def training_status(env_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TrainingRun)
        .where(TrainingRun.env_id == env_id)
        .order_by(desc(TrainingRun.created_at))
        .limit(1)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(404, "No training runs found")
    return await training_service.get_status(run.id, db)


@router.get("/train/run/{run_id}/status")
async def training_run_status(run_id: int, db: AsyncSession = Depends(get_db)):
    return await training_service.get_status(run_id, db)


@router.get("/train/{env_id}/curve")
async def training_curve(env_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TrainingRun)
        .where(TrainingRun.env_id == env_id)
        .order_by(desc(TrainingRun.created_at))
        .limit(1)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(404, "No training runs found")
    return await training_service.get_curve(run.id, db)


@router.get("/train/{env_id}/replay")
async def training_replay(env_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TrainingRun)
        .where(TrainingRun.env_id == env_id, TrainingRun.status == "completed")
        .order_by(desc(TrainingRun.created_at))
        .limit(1)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(404, "No completed training runs found")

    output_dir = os.path.abspath(os.path.join(
        os.getenv("DATA_DIR", "./data"), "trained_models", f"run_{run.id}"
    ))
    replay_path = os.path.join(output_dir, "replay.json")
    if not os.path.exists(replay_path):
        raise HTTPException(404, "No replay data found")

    try:
        with open(replay_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        raise HTTPException(500, "Failed to read replay data")


@router.get("/train/{env_id}/model")
async def download_model(env_id: int, db: AsyncSession = Depends(get_db)):
    from fastapi.responses import FileResponse as FR

    result = await db.execute(
        select(TrainingRun)
        .where(TrainingRun.env_id == env_id, TrainingRun.status == "completed")
        .order_by(desc(TrainingRun.completed_at))
        .limit(1)
    )
    run = result.scalar_one_or_none()
    if not run or not run.model_path:
        raise HTTPException(404, "No trained model found")
    if not os.path.exists(run.model_path):
        raise HTTPException(404, "Model file not found on disk")

    return FR(
        run.model_path,
        media_type="application/zip",
        filename=f"model_env{env_id}_{run.algorithm}.zip",
    )


# ──────────────────────────────────────────────────
#  REMOTE STEP (Session Manager)
# ──────────────────────────────────────────────────

@router.post("/sessions")
async def create_session(data: dict, db: AsyncSession = Depends(get_db)):
    env_id = data.get("env_id")
    if not env_id:
        raise HTTPException(400, "env_id is required")

    result = await db.execute(select(RLEnvironment).where(RLEnvironment.id == env_id))
    env = result.scalar_one_or_none()
    if not env or not env.code:
        raise HTTPException(404, "Environment not found or has no code")

    try:
        sid = session_manager.create_session(env.code, env.id)
        return {"session_id": sid, "env_id": env.id, "env_name": env.name}
    except Exception as e:
        raise HTTPException(500, f"Failed to create session: {e}")


@router.post("/sessions/{session_id}/step")
async def session_step(session_id: str, data: dict):
    action = data.get("action")
    if action is None:
        raise HTTPException(400, "action is required")
    try:
        return session_manager.step(session_id, action)
    except KeyError:
        raise HTTPException(404, "Session not found")
    except Exception as e:
        raise HTTPException(500, f"Step failed: {e}")


@router.post("/sessions/{session_id}/reset")
async def session_reset(session_id: str, data: dict = None):
    data = data or {}
    seed = data.get("seed")
    try:
        return session_manager.reset(session_id, seed=seed)
    except KeyError:
        raise HTTPException(404, "Session not found")
    except Exception as e:
        raise HTTPException(500, f"Reset failed: {e}")


@router.delete("/sessions/{session_id}")
async def session_close(session_id: str):
    try:
        session_manager.close(session_id)
        return {"status": "closed"}
    except KeyError:
        raise HTTPException(404, "Session not found")


@router.get("/sessions")
async def list_sessions():
    return session_manager.list_sessions()


# ──────────────────────────────────────────────────
#  PAPER -> ENV
# ──────────────────────────────────────────────────

@router.post("/generate-from-paper")
@limiter.limit("3/minute")
async def generate_from_paper(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    auth_user: Optional[dict] = Depends(get_optional_user),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted")

    pdf_bytes = await file.read()
    if len(pdf_bytes) > 20 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 20MB)")

    paper_text = await paper_parser.parse_pdf_bytes(pdf_bytes)
    if not paper_text.strip():
        raise HTTPException(400, "Could not extract text from PDF")

    result = await paper_parser.generate_from_paper(paper_text)
    if "error" in result:
        raise HTTPException(422, result["error"])

    slug = _slugify(result.get("name", "paper-env"))
    existing = await db.execute(select(RLEnvironment).where(RLEnvironment.slug == slug))
    if existing.scalar_one_or_none():
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

    paper_user_id = await _resolve_user_id(db, auth_user)

    env = RLEnvironment(
        name=result.get("name", "Paper Environment"),
        slug=slug,
        description=result.get("description", ""),
        category=result.get("domain", "custom"),
        domain=result.get("domain", "custom"),
        observation_space=result.get("observation_space", ""),
        action_space=result.get("action_space", ""),
        reward_description=result.get("reward_description", ""),
        code=result.get("code", ""),
        env_spec_json=json.dumps(result.get("env_spec", {})),
        test_results_json=json.dumps(result.get("test_results", {})),
        difficulty=result.get("env_spec", {}).get("difficulty", "medium"),
        status="draft",
        ai_model_used=settings.anthropic_model,
        topic=f"From paper: {file.filename}",
        generation_log=f"Generated from uploaded paper: {file.filename}",
        user_id=paper_user_id,
    )
    db.add(env)
    await db.commit()
    await db.refresh(env)

    v = EnvVersion(env_id=env.id, version=1, code=env.code, spec_json=env.env_spec_json, change_summary="Generated from paper")
    db.add(v)
    await db.commit()

    return {
        "id": env.id,
        "slug": env.slug,
        "name": env.name,
        "test_results": result.get("test_results"),
    }


# ──────────────────────────────────────────────────
#  PUBLIC RESEARCH LAB
# ──────────────────────────────────────────────────

@router.post("/research/projects")
async def create_research_project(
    data: dict,
    db: AsyncSession = Depends(get_db),
    auth_user: Optional[dict] = Depends(get_optional_user),
):
    from app.models import ResearchProject
    from app.services.lab_service import lab_service
    from app.schemas import ExperimentConfig
    from pydantic import ValidationError

    title = data.get("title", "").strip()
    if not title:
        raise HTTPException(400, "title is required")

    research_user_id = await _resolve_user_id(db, auth_user)

    experiment_config_json: Optional[str] = None
    raw_cfg = data.get("experiment_config")
    if raw_cfg:
        try:
            cfg = ExperimentConfig.model_validate(raw_cfg)
            experiment_config_json = cfg.model_dump_json()
        except ValidationError as e:
            raise HTTPException(422, f"Invalid experiment_config: {e.errors()}")

    project = await lab_service.create_project(
        db, title,
        description=data.get("description", ""),
        topic=data.get("topic", ""),
        user_id=research_user_id,
        experiment_config_json=experiment_config_json,
    )

    return {"id": project.id, "title": project.title, "status": project.status}


@router.get("/research/projects")
async def list_research_projects(limit: int = 20, offset: int = 0, db: AsyncSession = Depends(get_db)):
    from app.models import ResearchProject

    query = select(ResearchProject).order_by(desc(ResearchProject.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    projects = result.scalars().all()

    total_q = select(func.count()).select_from(ResearchProject)
    total = (await db.execute(total_q)).scalar()

    return {
        "items": [
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "topic": p.topic,
                "status": p.status,
                "current_phase": p.current_phase,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in projects
        ],
        "total": total,
    }


@router.get("/research/projects/{project_id}")
async def get_research_project(project_id: int, db: AsyncSession = Depends(get_db)):
    from app.models import ResearchProject, AgentMessage, ResearchPaper
    from app.services.lab_service import lab_service

    result = await db.execute(select(ResearchProject).where(ResearchProject.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")

    msgs_result = await db.execute(
        select(AgentMessage).where(AgentMessage.project_id == project_id).order_by(AgentMessage.created_at)
    )
    messages = msgs_result.scalars().all()

    papers_result = await db.execute(
        select(ResearchPaper).where(ResearchPaper.project_id == project_id).order_by(desc(ResearchPaper.created_at))
    )
    papers = papers_result.scalars().all()

    refs = await lab_service.get_project_references(db, project_id)

    return {
        "id": project.id,
        "title": project.title,
        "description": project.description,
        "topic": project.topic,
        "status": project.status,
        "current_phase": project.current_phase,
        "selected_idea": project.selected_idea,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "messages": [
            {
                "id": m.id,
                "agent_name": m.agent_name,
                "content": m.content,
                "phase": m.phase,
                "round_num": m.round_num,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
        "papers": [
            {
                "id": p.id,
                "title": p.title,
                "abstract": p.abstract,
                "status": p.status,
                "version": p.version,
                "published": p.published,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in papers
        ],
        "references": refs,
    }


@router.post("/research/projects/{project_id}/upload-paper")
async def upload_paper_to_project(project_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    from app.models import ResearchProject, Article, ProjectReference

    result = await db.execute(select(ResearchProject).where(ResearchProject.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")

    content_bytes = await file.read()
    filename = file.filename or "uploaded_paper"

    if filename.lower().endswith(".pdf"):
        text = await paper_parser.parse_pdf_bytes(content_bytes)
    else:
        text = content_bytes.decode("utf-8", errors="replace")

    if not text.strip():
        raise HTTPException(400, "Could not extract content from file")

    article = Article(
        filename=filename,
        title=filename.rsplit(".", 1)[0],
        content=text,
        file_type=filename.rsplit(".", 1)[-1] if "." in filename else "txt",
        source="manual",
        is_processed=False,
    )
    db.add(article)
    await db.flush()

    ref = ProjectReference(project_id=project_id, article_id=article.id)
    db.add(ref)
    await db.commit()

    return {"article_id": article.id, "title": article.title, "project_id": project_id}


# ── GitHub Export ─────────────────────────────────────────

@router.post("/github/push/{env_id}")
async def github_push(
    env_id: int,
    body: dict,
    auth: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Push environment code to a new GitHub repository using the user's connected GitHub account."""
    import base64
    import httpx

    clerk_user_id = auth["clerk_user_id"]
    repo_name = body.get("repo_name", f"rl-env-{env_id}")
    description = body.get("description", "")
    is_private = body.get("private", False)

    result = await db.execute(select(RLEnvironment).where(RLEnvironment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(404, "Environment not found")

    clerk_secret = os.getenv("CLERK_SECRET_KEY", "")
    if not clerk_secret:
        raise HTTPException(500, "Server configuration error")

    async with httpx.AsyncClient(timeout=30) as client:
        # Get GitHub OAuth token from Clerk
        resp = await client.get(
            f"https://api.clerk.com/v1/users/{clerk_user_id}/oauth_access_tokens/github",
            headers={"Authorization": f"Bearer {clerk_secret}"},
        )
        if resp.status_code != 200:
            raise HTTPException(400, "GitHub not connected. Sign in with GitHub first.")
        tokens = resp.json()
        if not tokens:
            raise HTTPException(400, "No GitHub account connected. Sign in with GitHub to use this feature.")
        github_token = tokens[0]["token"]

    gh_headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        user_resp = await client.get("https://api.github.com/user", headers=gh_headers)
        if user_resp.status_code != 200:
            raise HTTPException(400, "GitHub token invalid. Try reconnecting your GitHub account.")
        gh_username = user_resp.json()["login"]

        repo_resp = await client.post(
            "https://api.github.com/user/repos",
            headers=gh_headers,
            json={"name": repo_name, "description": description, "private": is_private, "auto_init": False},
        )
        if repo_resp.status_code == 422:
            raise HTTPException(409, f"Repository '{repo_name}' already exists on GitHub.")
        if repo_resp.status_code not in (200, 201):
            raise HTTPException(400, f"Failed to create repository: {repo_resp.text}")
        repo_url = repo_resp.json()["html_url"]

        files = _prepare_github_files(env)

        for i, (path, content) in enumerate(files.items()):
            content_b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
            put_resp = await client.put(
                f"https://api.github.com/repos/{gh_username}/{repo_name}/contents/{path}",
                headers=gh_headers,
                json={"message": f"Add {path}" if i > 0 else "Initial commit from kualia.ai", "content": content_b64},
            )
            if put_resp.status_code not in (200, 201):
                logger.warning("Failed to push %s: %s", path, put_resp.text)

    return {"url": repo_url, "repo": f"{gh_username}/{repo_name}"}


def _prepare_github_files(env) -> dict:
    """Build the set of files to push to the GitHub repo."""
    slug = env.slug or f"env_{env.id}"
    safe_class = slug.replace("-", "_").title().replace("_", "") + "Env"
    spec = json.loads(env.env_spec_json) if env.env_spec_json else {}
    obs_type = spec.get("observation_space", {}).get("type", "Box")
    act_type = spec.get("action_space", {}).get("type", "Discrete")
    max_steps = spec.get("episode", {}).get("max_steps", 1000)

    files = {}

    files[f"{slug.replace('-', '_')}.py"] = env.code or "# Environment code\n"

    files["requirements.txt"] = "gymnasium>=0.29.0\nnumpy>=1.24.0\nstable-baselines3>=2.1.0\n"

    files["train.py"] = f'''"""Training script for {env.name}"""
from stable_baselines3 import PPO
import gymnasium as gym

# Register and create environment
from {slug.replace("-", "_")} import *

env_id = "custom/{slug}-v0"
try:
    env = gym.make(env_id)
except:
    # Fallback: instantiate directly
    env = {safe_class}()

model = PPO("MlpPolicy", env, verbose=1, n_steps=2048, batch_size=64)
model.learn(total_timesteps=50_000)
model.save("{slug.replace("-", "_")}_ppo")
print("Training complete! Model saved.")
'''

    files["README.md"] = f"""# {env.name}

{env.description or "A custom RL environment."}

## Specifications

| Property | Value |
|----------|-------|
| Domain | {env.domain or "general"} |
| Difficulty | {env.difficulty or "medium"} |
| Observation Space | {obs_type} |
| Action Space | {act_type} |
| Max Steps | {max_steps} |

## Quick Start

```bash
pip install -r requirements.txt
python train.py
```

## Usage

```python
from {slug.replace("-", "_")} import {safe_class}

env = {safe_class}()
obs, info = env.reset()

for _ in range({max_steps}):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        obs, info = env.reset()
```

---

*Generated by [kualia.ai](https://kualia.ai)*
"""

    return files


# ── Smart Suggestions (AI-driven quick actions) ─────────────────

@router.get("/builder/{env_id}/suggestions")
@limiter.limit("10/minute")
async def get_suggestions(request: Request, env_id: int, db: AsyncSession = Depends(get_db)):
    """Analyze env code + training results and return 4-6 smart next-step suggestions."""
    result = await db.execute(select(RLEnvironment).where(RLEnvironment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(404, "Environment not found")

    runs_result = await db.execute(
        select(TrainingRun).where(TrainingRun.env_id == env_id)
        .order_by(desc(TrainingRun.created_at)).limit(3)
    )
    runs = runs_result.scalars().all()

    training_ctx = ""
    has_completed_training = False
    best_reward = None
    best_success = None
    for run in runs:
        if run.status == "completed" and run.results_json:
            has_completed_training = True
            r = json.loads(run.results_json)
            reward = r.get("mean_reward")
            success = r.get("success_rate")
            if best_reward is None or (reward and reward > best_reward):
                best_reward = reward
            if best_success is None or (success and success > best_success):
                best_success = success
            training_ctx += (
                f"\n- {run.algorithm}: mean_reward={r.get('mean_reward')}, "
                f"success_rate={r.get('success_rate')}, "
                f"ep_length={r.get('mean_ep_length')}, "
                f"timesteps={r.get('total_timesteps')}"
            )

    spec = json.loads(env.env_spec_json) if env.env_spec_json else {}
    obs_space = spec.get("observation_space", {})
    act_space = spec.get("action_space", {})
    reward_fn = spec.get("reward_function", {})
    params = spec.get("parameters", {})

    prompt = (
        f"You are an RL environment design advisor. Analyze this environment and suggest "
        f"4-6 concrete next steps the user can take to improve it.\n\n"
        f"ENVIRONMENT:\n"
        f"- Name: {env.name}\n"
        f"- Domain: {env.domain}\n"
        f"- Difficulty: {env.difficulty}\n"
        f"- Description: {env.description or 'N/A'}\n"
        f"- Obs space: {env.observation_space}\n"
        f"- Action space: {env.action_space}\n"
        f"- Reward: {env.reward_description}\n"
        f"- Parameters: {json.dumps(params)[:500]}\n\n"
    )

    if has_completed_training:
        prompt += f"TRAINING RESULTS:{training_ctx}\n\n"

    prompt += (
        f"Based on the environment's current state"
        f"{' and training results' if has_completed_training else ''}, "
        f"suggest exactly 5 next steps. Each suggestion must be:\n"
        f"- A short action label (max 6 words) shown as a button\n"
        f"- A chat message (1-2 sentences) that will be sent to the builder agent\n"
        f"- A category: one of 'iterate', 'difficulty', 'training', 'experiment'\n\n"
        f"Rules for suggestions:\n"
        f"- Be SPECIFIC to this environment, not generic advice\n"
        f"- If training succeeded (high success rate), suggest harder challenges\n"
        f"- If training struggled, suggest making rewards denser or simplifying\n"
        f"- Always include at least one env modification and one training suggestion\n"
        f"- If no training yet, focus on env improvements and first training\n"
        f"- Suggestions should be diverse: mix difficulty, reward, obs, action changes\n\n"
        f"Return ONLY a JSON array:\n"
        f'[{{"label": "...", "message": "...", "category": "..."}}]\n'
        f"No other text."
    )

    from app.services.ai_service import ai_service
    try:
        response = await ai_service._call_claude(
            "You are an RL advisor. Return only valid JSON arrays.",
            prompt,
            model=settings.anthropic_model,
            max_tokens=2000,
        )
    except Exception:
        try:
            response = await ai_service._call_kimi(
                "You are an RL advisor. Return only valid JSON arrays.",
                prompt,
                max_tokens=2000,
            )
        except Exception:
            return []

    import re as _re
    match = _re.search(r'\[.*\]', response, _re.DOTALL)
    if match:
        try:
            suggestions = json.loads(match.group())
            valid = []
            for s in suggestions[:6]:
                if isinstance(s, dict) and "label" in s and "message" in s:
                    valid.append({
                        "label": str(s["label"])[:40],
                        "message": str(s["message"])[:300],
                        "category": str(s.get("category", "iterate"))[:20],
                    })
            return valid
        except json.JSONDecodeError:
            pass

    return []
