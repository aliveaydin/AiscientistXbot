from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from app.database import get_db, async_session
from app.models import ResearchProject, ProjectReference, AgentMessage, AgentWork, ResearchPaper, Article
from app.schemas import (
    ResearchProjectCreate, ResearchProjectResponse,
    AgentMessageResponse, AgentWorkResponse, ResearchPaperResponse,
    ProjectReferenceResponse,
)
from app.services.lab_service import lab_service, AGENTS, PHASES
from app.services.article_service import ArticleService

router = APIRouter(prefix="/api/lab", tags=["Research Lab"])


@router.get("/agents")
async def get_agents():
    """Get all lab agent profiles."""
    return {
        key: {"name": a["name"], "role": a["role"], "color": a["color"]}
        for key, a in AGENTS.items()
    }


@router.get("/phases")
async def get_phases():
    """Get all research phases."""
    return PHASES


@router.get("/projects", response_model=list[ResearchProjectResponse])
async def get_projects(db: AsyncSession = Depends(get_db)):
    """List all research projects."""
    result = await db.execute(
        select(ResearchProject).order_by(ResearchProject.created_at.desc())
    )
    projects = result.scalars().all()

    out = []
    for p in projects:
        msg_count = await db.execute(
            select(func.count(AgentMessage.id)).where(AgentMessage.project_id == p.id)
        )
        work_count = await db.execute(
            select(func.count(AgentWork.id)).where(AgentWork.project_id == p.id)
        )
        ref_count = await db.execute(
            select(func.count(ProjectReference.id)).where(ProjectReference.project_id == p.id)
        )
        data = ResearchProjectResponse.model_validate(p)
        data.message_count = msg_count.scalar() or 0
        data.work_count = work_count.scalar() or 0
        data.reference_count = ref_count.scalar() or 0
        out.append(data)
    return out


@router.post("/projects", response_model=ResearchProjectResponse)
async def create_project(
    req: ResearchProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new research project."""
    project = await lab_service.create_project(db, req.title, req.description, req.topic)
    return ResearchProjectResponse.model_validate(project)


@router.get("/projects/{project_id}")
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    """Get project details."""
    detail = await lab_service.get_project_detail(db, project_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Project not found")
    return detail


@router.post("/projects/{project_id}/run-phase")
async def run_next_phase(project_id: int, db: AsyncSession = Depends(get_db)):
    """Run the next phase of the research pipeline."""
    result = await lab_service.run_next_phase(db, project_id)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/projects/{project_id}/run-all")
async def run_all_phases_endpoint(project_id: int, background_tasks: BackgroundTasks):
    """Run all remaining phases in the background."""

    async def _run():
        async with async_session() as db:
            await lab_service.run_all_phases(db, project_id)

    background_tasks.add_task(_run)
    return {"message": "All phases started in background", "project_id": project_id}


@router.get("/projects/{project_id}/chatboard", response_model=list[AgentMessageResponse])
async def get_chatboard(project_id: int, db: AsyncSession = Depends(get_db)):
    """Get all chatboard messages for a project."""
    messages = await lab_service.get_chatboard(db, project_id)
    return messages


@router.get("/projects/{project_id}/agent/{agent_name}/work", response_model=list[AgentWorkResponse])
async def get_agent_work(
    project_id: int,
    agent_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all work items for a specific agent in a project."""
    if agent_name not in AGENTS:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {agent_name}")
    works = await lab_service.get_agent_work(db, project_id, agent_name)
    return works


@router.get("/projects/{project_id}/paper", response_model=ResearchPaperResponse)
async def get_paper(project_id: int, db: AsyncSession = Depends(get_db)):
    """Get the research paper for a project."""
    paper = await lab_service.get_paper(db, project_id)
    if not paper:
        raise HTTPException(status_code=404, detail="No paper generated yet")
    return paper


@router.get("/projects/{project_id}/references")
async def get_project_references(project_id: int, db: AsyncSession = Depends(get_db)):
    """Get all reference papers linked to a project."""
    refs = await lab_service.get_project_references(db, project_id)
    return refs


@router.post("/projects/{project_id}/upload-doc")
async def upload_project_document(
    project_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document and link it as a reference to a project."""
    result = await db.execute(select(ResearchProject).where(ResearchProject.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    from pathlib import Path
    ext = Path(file.filename).suffix.lower()
    if ext not in ArticleService.SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    content = await file.read()
    article = await ArticleService.upload_article(db, file.filename, content)

    db.add(ProjectReference(project_id=project_id, article_id=article.id))
    await db.commit()

    return {"success": True, "article_id": article.id, "title": article.title or article.filename}


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a research project and all its data."""
    deleted = await lab_service.delete_project(db, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted"}
