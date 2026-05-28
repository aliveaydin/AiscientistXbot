"""
Credit service for token-based billing.

Every LLM call's actual cost is multiplied by MARKUP (10x) and deducted from
the user's dollar-credit balance.  Training runs are charged per 1K timesteps.
"""

import json
import logging
import os
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, SubscriptionPlan, CreditTransaction, RLEnvironment, ResearchProject

logger = logging.getLogger("credits")

ADMIN_EMAILS = [e.strip() for e in os.getenv("ADMIN_EMAILS", "aliveaydin@gmail.com").split(",") if e.strip()]

# Kimi K2.5 pricing (per token)
KIMI_INPUT_PRICE = 0.60 / 1_000_000   # $0.60 per 1M input tokens
KIMI_OUTPUT_PRICE = 2.40 / 1_000_000  # $2.40 per 1M output tokens

# Claude Sonnet pricing
CLAUDE_INPUT_PRICE = 3.00 / 1_000_000
CLAUDE_OUTPUT_PRICE = 15.00 / 1_000_000

# Claude Opus 4.8 pricing (primary model)
CLAUDE_OPUS_INPUT_PRICE = 15.00 / 1_000_000
CLAUDE_OPUS_OUTPUT_PRICE = 75.00 / 1_000_000

# OpenAI GPT-4 pricing
GPT4_INPUT_PRICE = 30.00 / 1_000_000
GPT4_OUTPUT_PRICE = 60.00 / 1_000_000

MARKUP = 10  # 10x markup on actual cost

TRAINING_COST_PER_1K_STEPS = 0.10  # $0.10 per 1K timesteps


class UsageAccumulator:
    """Collects token usage across multiple LLM calls within one operation."""

    def __init__(self):
        self.calls: list[dict] = []
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    def add(self, prompt_tokens: int, completion_tokens: int, model: str = "kimi-k2.5"):
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.calls.append({
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        })

    def actual_cost(self) -> float:
        """Calculate actual cost based on model pricing."""
        total = 0
        for c in self.calls:
            model = c["model"].lower()
            if "kimi" in model:
                total += c["prompt_tokens"] * KIMI_INPUT_PRICE + c["completion_tokens"] * KIMI_OUTPUT_PRICE
            elif "opus" in model:
                total += c["prompt_tokens"] * CLAUDE_OPUS_INPUT_PRICE + c["completion_tokens"] * CLAUDE_OPUS_OUTPUT_PRICE
            elif "claude" in model:
                total += c["prompt_tokens"] * CLAUDE_INPUT_PRICE + c["completion_tokens"] * CLAUDE_OUTPUT_PRICE
            else:
                total += c["prompt_tokens"] * GPT4_INPUT_PRICE + c["completion_tokens"] * GPT4_OUTPUT_PRICE
        return total

    def billed_cost(self) -> float:
        return self.actual_cost() * MARKUP

    def to_dict(self) -> dict:
        return {
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "actual_cost": round(self.actual_cost(), 6),
            "billed_cost": round(self.billed_cost(), 6),
            "calls": self.calls,
        }


class CreditService:

    async def _is_admin(self, user_id: int, db: AsyncSession) -> bool:
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        return bool(user and user.email and user.email.lower() in [e.lower() for e in ADMIN_EMAILS])

    async def get_balance(self, user_id: int, db: AsyncSession) -> float:
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        return user.credit_balance if user else 0

    async def get_plan(self, user_id: int, db: AsyncSession) -> Optional[dict]:
        user = (await db.execute(
            select(User).where(User.id == user_id)
        )).scalar_one_or_none()
        if not user or not user.plan_id:
            return None
        plan = (await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == user.plan_id)
        )).scalar_one_or_none()
        if not plan:
            return None
        return {
            "id": plan.id,
            "name": plan.name,
            "display_name": plan.display_name,
            "price_monthly": plan.price_monthly,
            "monthly_credits": plan.monthly_credits,
            "max_environments": plan.max_environments,
            "max_training_steps": plan.max_training_steps,
            "pdf_download": plan.pdf_download,
            "github_export": plan.github_export,
            "can_buy_credits": plan.can_buy_credits,
        }

    async def check_credits(self, user_id: int, required: float, db: AsyncSession) -> dict:
        """Check if user has enough credits. Returns {ok, balance, required, shortfall}."""
        if await self._is_admin(user_id, db):
            return {"ok": True, "balance": 999999, "required": required, "shortfall": 0}
        balance = await self.get_balance(user_id, db)
        ok = balance >= required
        return {
            "ok": ok,
            "balance": round(balance, 4),
            "required": round(required, 4),
            "shortfall": round(max(0, required - balance), 4),
        }

    async def check_plan_limit(self, user_id: int, limit_type: str, db: AsyncSession) -> dict:
        """Check plan-level limits (max environments, max training steps, etc.)."""
        if await self._is_admin(user_id, db):
            return {"ok": True, "limit": -1, "current": 0, "max_steps": 99999999}
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user or not user.plan_id:
            return {"ok": False, "reason": "no_plan", "limit": 0, "current": 0}

        plan = (await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == user.plan_id)
        )).scalar_one_or_none()
        if not plan:
            return {"ok": False, "reason": "plan_not_found", "limit": 0, "current": 0}

        if limit_type == "environments":
            if plan.max_environments == -1:
                return {"ok": True, "limit": -1, "current": 0}
            count = (await db.execute(
                select(func.count(RLEnvironment.id)).where(RLEnvironment.user_id == user_id)
            )).scalar() or 0
            return {
                "ok": count < plan.max_environments,
                "limit": plan.max_environments,
                "current": count,
                "reason": "limit_reached" if count >= plan.max_environments else None,
            }

        if limit_type == "training_steps":
            return {
                "ok": True,
                "max_steps": plan.max_training_steps,
            }

        if limit_type == "pdf_download":
            return {"ok": plan.pdf_download}

        if limit_type == "github_export":
            return {"ok": plan.github_export}

        if limit_type == "buy_credits":
            return {"ok": plan.can_buy_credits}

        return {"ok": True}

    async def consume_credits(
        self,
        user_id: int,
        amount: float,
        operation: str,
        db: AsyncSession,
        resource_id: Optional[int] = None,
        details: Optional[dict] = None,
    ) -> dict:
        """Deduct credits from user balance. Returns {ok, balance_before, balance_after, charged}."""
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            return {"ok": False, "error": "user_not_found"}

        if user.email and user.email.lower() in [e.lower() for e in ADMIN_EMAILS]:
            logger.info("Admin user %d (%s) — skipping credit deduction for %s ($%.4f)", user_id, user.email, operation, amount)
            return {"ok": True, "balance_before": user.credit_balance, "balance_after": user.credit_balance, "charged": 0}

        balance_before = user.credit_balance
        charged = round(amount, 6)

        if balance_before < charged:
            return {"ok": False, "error": "insufficient_credits", "balance": balance_before, "required": charged}

        user.credit_balance = round(balance_before - charged, 6)
        balance_after = user.credit_balance

        tx = CreditTransaction(
            user_id=user_id,
            amount=-charged,
            balance_after=balance_after,
            operation=operation,
            resource_id=resource_id,
            details_json=json.dumps(details) if details else None,
        )
        db.add(tx)
        await db.commit()

        logger.info(
            "Credit consumed: user=%d op=%s amount=$%.4f balance=$%.4f->$%.4f",
            user_id, operation, charged, balance_before, balance_after,
        )

        # Low-credit email alert (fire once when crossing $1 threshold)
        if balance_after < 1.0 and balance_before >= 1.0:
            try:
                from app.services.email_service import email_service
                if user.email and getattr(user, "email_notifications", True):
                    await email_service.send_transactional(
                        to=user.email, template="credits_low",
                        data={"balance": f"{balance_after:.2f}"},
                        user_id=user_id,
                    )
            except Exception:
                pass

        return {"ok": True, "balance_before": balance_before, "balance_after": balance_after, "charged": charged}

    async def add_credits(
        self,
        user_id: int,
        amount: float,
        operation: str,
        db: AsyncSession,
        details: Optional[dict] = None,
    ) -> dict:
        """Add credits to user balance."""
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            return {"ok": False, "error": "user_not_found"}

        balance_before = user.credit_balance
        user.credit_balance = round(balance_before + amount, 6)
        balance_after = user.credit_balance

        tx = CreditTransaction(
            user_id=user_id,
            amount=round(amount, 6),
            balance_after=balance_after,
            operation=operation,
            details_json=json.dumps(details) if details else None,
        )
        db.add(tx)
        await db.commit()

        logger.info(
            "Credit added: user=%d op=%s amount=$%.4f balance=$%.4f->$%.4f",
            user_id, operation, amount, balance_before, balance_after,
        )
        return {"ok": True, "balance_before": balance_before, "balance_after": balance_after, "added": amount}

    async def get_usage_history(
        self,
        user_id: int,
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """Get credit transaction history for a user."""
        total = (await db.execute(
            select(func.count(CreditTransaction.id)).where(CreditTransaction.user_id == user_id)
        )).scalar() or 0

        rows = (await db.execute(
            select(CreditTransaction)
            .where(CreditTransaction.user_id == user_id)
            .order_by(CreditTransaction.created_at.desc())
            .offset(offset).limit(limit)
        )).scalars().all()

        return {
            "total": total,
            "transactions": [{
                "id": t.id,
                "amount": t.amount,
                "balance_after": t.balance_after,
                "operation": t.operation,
                "resource_id": t.resource_id,
                "details": json.loads(t.details_json) if t.details_json else None,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            } for t in rows],
        }

    async def get_monthly_usage(self, user_id: int, db: AsyncSession) -> dict:
        """Get current month's credit usage summary."""
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        rows = (await db.execute(
            select(CreditTransaction)
            .where(
                CreditTransaction.user_id == user_id,
                CreditTransaction.amount < 0,
                CreditTransaction.created_at >= month_start,
            )
        )).scalars().all()

        by_operation: dict[str, float] = {}
        total_spent = 0
        for t in rows:
            op = t.operation
            spent = abs(t.amount)
            by_operation[op] = by_operation.get(op, 0) + spent
            total_spent += spent

        return {
            "month": now.strftime("%Y-%m"),
            "total_spent": round(total_spent, 4),
            "by_operation": {k: round(v, 4) for k, v in by_operation.items()},
            "transaction_count": len(rows),
        }

    @staticmethod
    def calculate_training_cost(total_timesteps: int) -> float:
        """Calculate training cost in credits (USD)."""
        return round((total_timesteps / 1000) * TRAINING_COST_PER_1K_STEPS, 4)

    @staticmethod
    def estimate_operation_cost(operation: str) -> float:
        """Rough cost estimate for pre-check (based on measurements)."""
        estimates = {
            "env_generation": 0.40,
            "builder_chat": 0.10,
            "research_hypothesis": 0.10,
            "research_experiment": 0.50,
            "research_paper": 0.15,
            "paper_from_env": 0.30,
            "reference_search": 0.02,
        }
        return estimates.get(operation, 0.10)


credit_service = CreditService()
