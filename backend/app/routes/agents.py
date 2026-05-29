from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any

from app.services.agent_registry import agent_registry
from app.auth import require_admin

router = APIRouter(prefix="/api/agents", tags=["Agents"], dependencies=[Depends(require_admin)])


@router.get("")
async def list_agents():
    return {"agents": agent_registry.list_agents()}


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    agent = agent_registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    return agent


class UpdateParamRequest(BaseModel):
    key: str
    value: Any


@router.put("/{agent_id}/param")
async def update_param(agent_id: str, req: UpdateParamRequest):
    ok = agent_registry.update_agent_param(agent_id, req.key, req.value)
    if not ok:
        raise HTTPException(404, "Agent or param not found")
    return {"updated": True, "agent_id": agent_id, "key": req.key, "value": req.value}


class UpdateStatusRequest(BaseModel):
    status: str


@router.put("/{agent_id}/status")
async def update_status(agent_id: str, req: UpdateStatusRequest):
    if req.status not in ("active", "paused", "disabled"):
        raise HTTPException(400, "Invalid status")
    ok = agent_registry.update_agent_status(agent_id, req.status)
    if not ok:
        raise HTTPException(404, "Agent not found")
    return {"updated": True, "agent_id": agent_id, "status": req.status}
