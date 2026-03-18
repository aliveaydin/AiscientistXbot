import json
import logging
from typing import Optional, Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models import RLEnvironment, BuilderConversation, EnvVersion
from app.services.architect_service import architect_service
from app.services.sandbox_runner import sandbox_runner

logger = logging.getLogger("builder")


class BuilderService:
    """Manages iterative environment design conversations.

    Wraps ArchitectService.iterate_env with conversation persistence,
    version tracking, and breaking-change detection.
    """

    async def start_session(
        self, env_id: int, db: AsyncSession
    ) -> Dict[str, Any]:
        """Initialise or resume a builder session for an environment."""
        result = await db.execute(
            select(RLEnvironment).where(RLEnvironment.id == env_id)
        )
        env = result.scalar_one_or_none()
        if env is None:
            raise ValueError(f"Environment {env_id} not found")

        msg_result = await db.execute(
            select(BuilderConversation)
            .where(BuilderConversation.env_id == env_id)
            .order_by(BuilderConversation.created_at)
        )
        messages = msg_result.scalars().all()

        return {
            "env_id": env.id,
            "name": env.name,
            "version": env.version,
            "has_history": len(messages) > 0,
            "message_count": len(messages),
            "test_results": json.loads(env.test_results_json) if env.test_results_json else None,
        }

    async def iterate(
        self, env_id: int, user_message: str, db: AsyncSession
    ) -> Dict[str, Any]:
        """Send a user message and get an updated environment back."""
        result = await db.execute(
            select(RLEnvironment).where(RLEnvironment.id == env_id)
        )
        env = result.scalar_one_or_none()
        if env is None:
            raise ValueError(f"Environment {env_id} not found")

        user_msg = BuilderConversation(
            env_id=env_id,
            role="user",
            content=user_message,
            version_snapshot=env.version,
        )
        db.add(user_msg)

        iterated = await architect_service.iterate_env(
            env.code or "",
            env.env_spec_json or "{}",
            user_message,
        )

        new_code = iterated.get("updated_code", env.code)
        new_spec = iterated.get("updated_spec", {})
        change_summary = iterated.get("change_summary", "Updated")
        breaking = iterated.get("breaking_changes", [])

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
                "change_summary": change_summary,
                "breaking_changes": breaking,
                "test_results": test_results,
            }),
            version_snapshot=env.version,
        )
        db.add(assistant_msg)

        ver = EnvVersion(
            env_id=env_id,
            version=env.version,
            code=new_code,
            spec_json=env.env_spec_json,
            change_summary=change_summary,
        )
        db.add(ver)
        await db.commit()

        return {
            "version": env.version,
            "change_summary": change_summary,
            "breaking_changes": breaking,
            "test_results": test_results,
            "code": new_code,
            "spec": new_spec,
        }

    async def get_history(
        self, env_id: int, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Return full conversation + version history."""
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

    async def rollback(
        self, env_id: int, target_version: int, db: AsyncSession
    ) -> Dict[str, Any]:
        """Revert environment to a previous version."""
        result = await db.execute(
            select(RLEnvironment).where(RLEnvironment.id == env_id)
        )
        env = result.scalar_one_or_none()
        if env is None:
            raise ValueError(f"Environment {env_id} not found")

        ver_result = await db.execute(
            select(EnvVersion).where(
                EnvVersion.env_id == env_id,
                EnvVersion.version == target_version,
            )
        )
        ver = ver_result.scalar_one_or_none()
        if ver is None:
            raise ValueError(f"Version {target_version} not found for env {env_id}")

        env.code = ver.code
        env.env_spec_json = ver.spec_json
        env.version = target_version

        test_results = (
            await sandbox_runner.run_all_tests(ver.code)
            if ver.code
            else {"passed": 0, "failed": 8, "total": 8, "tests": []}
        )
        env.test_results_json = json.dumps(test_results)

        rollback_msg = BuilderConversation(
            env_id=env_id,
            role="system",
            content=f"Rolled back to version {target_version}",
            version_snapshot=target_version,
        )
        db.add(rollback_msg)
        await db.commit()

        return {"version": target_version, "test_results": test_results}

    async def get_versions(
        self, env_id: int, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """List all versions for an environment."""
        result = await db.execute(
            select(EnvVersion)
            .where(EnvVersion.env_id == env_id)
            .order_by(desc(EnvVersion.version))
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


builder_service = BuilderService()
