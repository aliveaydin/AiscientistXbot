from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from typing import Optional
import json
from app.database import get_db, async_session
from app.models import ResearchProject, ProjectReference, AgentMessage, AgentWork, ResearchPaper, Article, RLEnvironment, TrainingRun
from app.schemas import (
    ResearchProjectCreate, ResearchProjectResponse,
    AgentMessageResponse, AgentWorkResponse, ResearchPaperResponse,
)
from app.services.lab_service import lab_service, AGENTS, PHASES
from app.services.article_service import ArticleService
from app.auth import get_current_user, get_optional_user

router = APIRouter(prefix="/api/lab", tags=["Research Lab"])


async def _resolve_user_id(db: AsyncSession, auth_user: Optional[dict]) -> Optional[int]:
    if not auth_user:
        return None
    from app.models import User
    clerk_id = auth_user.get("clerk_user_id") or auth_user.get("sub")
    if not clerk_id:
        return None
    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = result.scalar_one_or_none()
    return user.id if user else None


@router.get("/agents")
async def get_agents():
    return {
        key: {"name": a["name"], "role": a["role"], "color": a["color"]}
        for key, a in AGENTS.items()
    }


@router.get("/phases")
async def get_phases():
    return PHASES


@router.get("/projects", response_model=list[ResearchProjectResponse])
async def get_projects(db: AsyncSession = Depends(get_db)):
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
    auth_user: Optional[dict] = Depends(get_optional_user),
):
    user_id = await _resolve_user_id(db, auth_user)
    project = await lab_service.create_project(db, req.title, req.description, req.topic, user_id=user_id)
    return ResearchProjectResponse.model_validate(project)


@router.get("/projects/{project_id}")
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    detail = await lab_service.get_project_detail(db, project_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Project not found")
    return detail


@router.post("/projects/{project_id}/run-phase")
async def run_next_phase(project_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResearchProject).where(ResearchProject.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.status == "completed":
        raise HTTPException(status_code=400, detail="Project already completed")
    if getattr(project, "phase_running", False):
        raise HTTPException(status_code=409, detail="A phase is already running")

    current_phase = project.current_phase

    async def _run(pid: int):
        async with async_session() as bg_db:
            await lab_service.run_next_phase(bg_db, pid)

    background_tasks.add_task(_run, project_id)
    return {"message": f"Phase '{current_phase}' started in background", "phase": current_phase, "project_id": project_id}


@router.post("/projects/{project_id}/run-all")
async def run_all_phases_endpoint(project_id: int, background_tasks: BackgroundTasks):
    async def _run():
        async with async_session() as db:
            await lab_service.run_all_phases(db, project_id)

    background_tasks.add_task(_run)
    return {"message": "All phases started in background", "project_id": project_id}


@router.get("/projects/{project_id}/chatboard", response_model=list[AgentMessageResponse])
async def get_chatboard(project_id: int, db: AsyncSession = Depends(get_db)):
    messages = await lab_service.get_chatboard(db, project_id)
    return messages


@router.get("/projects/{project_id}/agent/{agent_name}/work", response_model=list[AgentWorkResponse])
async def get_agent_work(project_id: int, agent_name: str, db: AsyncSession = Depends(get_db)):
    if agent_name not in AGENTS:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {agent_name}")
    works = await lab_service.get_agent_work(db, project_id, agent_name)
    return works


@router.get("/projects/{project_id}/paper", response_model=ResearchPaperResponse)
async def get_paper(project_id: int, db: AsyncSession = Depends(get_db)):
    paper = await lab_service.get_paper(db, project_id)
    if not paper:
        raise HTTPException(status_code=404, detail="No paper generated yet")
    return paper


@router.get("/projects/{project_id}/references")
async def get_project_references(project_id: int, db: AsyncSession = Depends(get_db)):
    refs = await lab_service.get_project_references(db, project_id)
    return refs


@router.get("/projects/{project_id}/environments")
async def get_project_environments(project_id: int, db: AsyncSession = Depends(get_db)):
    return await lab_service.get_project_environments(db, project_id)


@router.get("/projects/{project_id}/training-runs")
async def get_project_training_runs(project_id: int, db: AsyncSession = Depends(get_db)):
    return await lab_service.get_project_training_runs(db, project_id)


@router.post("/projects/{project_id}/upload-doc")
async def upload_project_document(
    project_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
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


@router.post("/projects/{project_id}/paper/publish")
async def publish_paper(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ResearchPaper).where(ResearchPaper.project_id == project_id).order_by(ResearchPaper.version.desc())
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="No paper found for this project")

    paper.published = True
    paper.published_at = datetime.utcnow()
    await db.commit()
    return {"success": True, "paper_id": paper.id, "title": paper.title}


@router.post("/projects/{project_id}/paper/unpublish")
async def unpublish_paper(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ResearchPaper).where(ResearchPaper.project_id == project_id).order_by(ResearchPaper.version.desc())
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="No paper found for this project")

    paper.published = False
    paper.published_at = None
    await db.commit()
    return {"success": True}


@router.post("/paper-from-env/{env_id}")
async def paper_from_env(
    env_id: int,
    background_tasks: BackgroundTasks,
    topic: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    auth_user: Optional[dict] = Depends(get_optional_user),
):
    user_id = await _resolve_user_id(db, auth_user)

    from app.models import RLEnvironment
    env_result = await db.execute(select(RLEnvironment).where(RLEnvironment.id == env_id))
    env = env_result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    title = topic or f"Research: {env.name}"
    project = ResearchProject(
        title=title, description=f"Paper generated from environment: {env.name}",
        topic=topic or env.description or env.name,
        user_id=user_id, current_phase="analyze", status="active",
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    project_id = project.id

    async def _run(pid: int, eid: int, t: Optional[str], uid: Optional[int]):
        async with async_session() as bg_db:
            await lab_service._paper_from_env_pipeline(bg_db, pid, eid, t, uid)

    background_tasks.add_task(_run, project_id, env_id, topic, user_id)

    return {"project_id": project_id, "title": title, "status": "started"}


@router.get("/projects/{project_id}/paper/download")
async def download_paper(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ResearchPaper).where(ResearchPaper.project_id == project_id)
        .order_by(ResearchPaper.version.desc())
    )
    paper = result.scalars().first()
    if not paper:
        raise HTTPException(status_code=404, detail="No paper found")

    import markdown as md
    paper_html = md.markdown(paper.content or "", extensions=["tables", "fenced_code"])

    chart_html = await _generate_training_charts(db, project_id)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{paper.title}</title>
<style>
@page {{ margin: 2.5cm; size: A4; }}
body {{ font-family: 'Times New Roman', 'Noto Serif', Georgia, serif; font-size: 11pt;
  line-height: 1.6; color: #111; max-width: 800px; margin: 0 auto; padding: 40px 20px; }}
h1 {{ font-size: 18pt; text-align: center; margin: 0 0 10px; line-height: 1.3; }}
h2 {{ font-size: 14pt; margin-top: 24pt; border-bottom: 1px solid #ccc; padding-bottom: 4pt; }}
h3 {{ font-size: 12pt; margin-top: 18pt; }}
p {{ text-align: justify; margin: 6pt 0; }}
table {{ border-collapse: collapse; width: 100%; margin: 12pt 0; font-size: 10pt; }}
th, td {{ border: 1px solid #666; padding: 6px 10px; text-align: left; }}
th {{ background: #f0f0f0; font-weight: bold; }}
.abstract {{ font-style: italic; margin: 16pt 20pt; padding: 12pt; background: #f9f9f9;
  border-left: 3px solid #666; }}
.charts {{ page-break-inside: avoid; margin: 20pt 0; }}
.chart-img {{ max-width: 100%; height: auto; margin: 8pt 0; }}
code {{ font-family: 'Courier New', monospace; font-size: 9pt; background: #f5f5f5; padding: 1px 4px; }}
pre {{ background: #f5f5f5; padding: 10px; border: 1px solid #ddd; overflow-x: auto; font-size: 9pt; }}
@media print {{
  body {{ padding: 0; }}
  .no-print {{ display: none; }}
}}
.print-btn {{ position: fixed; top: 20px; right: 20px; background: #333; color: white;
  border: none; padding: 10px 20px; cursor: pointer; font-size: 14px; border-radius: 6px;
  z-index: 1000; }}
.print-btn:hover {{ background: #555; }}
</style>
</head>
<body>
<button class="print-btn no-print" onclick="window.print()">Download as PDF (Ctrl+P)</button>
<h1>{paper.title}</h1>
<p style="text-align:center; color:#666; font-size:10pt;">
  Generated by Kualia AI Research Lab | {datetime.utcnow().strftime('%B %d, %Y')}
</p>
{f'<div class="abstract"><strong>Abstract.</strong> {paper.abstract}</div>' if paper.abstract else ''}
{paper_html}
{chart_html}
</body>
</html>"""

    return HTMLResponse(content=html, headers={
        "Content-Disposition": f'inline; filename="{paper.title[:60].replace(chr(34), "")}.html"'
    })


async def _generate_training_charts(db: AsyncSession, project_id: int) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import io, base64

    env_ids_result = await db.execute(
        select(RLEnvironment.id, RLEnvironment.name).where(RLEnvironment.research_project_id == project_id)
    )
    env_map = {r[0]: r[1] for r in env_ids_result.fetchall()}
    if not env_map:
        return ""

    runs_result = await db.execute(
        select(TrainingRun).where(
            TrainingRun.env_id.in_(list(env_map.keys())),
            TrainingRun.status == "completed",
        ).order_by(TrainingRun.created_at)
    )
    runs = runs_result.scalars().all()
    chart_runs = [(run, env_map.get(run.env_id, f"Env {run.env_id}"))
                  for run in runs if run.training_curve_json]

    if not chart_runs:
        return ""

    charts_html = '<div class="charts"><h2>Training Curves</h2>'

    fig, ax = plt.subplots(figsize=(8, 4))
    for run, env_name in chart_runs:
        curve = json.loads(run.training_curve_json)
        rewards = [p.get("mean_reward", 0) for p in curve]
        steps = [p.get("timestep", i * 1000) for i, p in enumerate(curve)]
        ax.plot(steps, rewards, label=f"{env_name} ({run.algorithm})", linewidth=1.5)

    ax.set_xlabel("Training Steps", fontsize=10)
    ax.set_ylabel("Mean Reward", fontsize=10)
    ax.set_title("Training Reward Curves", fontsize=12)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode()
    charts_html += f'<img class="chart-img" src="data:image/png;base64,{img_b64}" alt="Training Curves" />'

    charts_html += "</div>"
    return charts_html


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await lab_service.delete_project(db, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted"}
