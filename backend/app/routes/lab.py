from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from app.rate_limit import limiter
from typing import Optional
import json
from app.database import get_db, async_session
from app.models import ResearchProject, ProjectReference, AgentMessage, AgentWork, ResearchPaper, Article, RLEnvironment, TrainingRun, EnvVersion
from app.schemas import (
    ResearchProjectCreate, ResearchProjectResponse,
    AgentMessageResponse, AgentWorkResponse, ResearchPaperResponse,
)
from app.services.lab_service import lab_service, AGENTS, PHASES, _active_usage_acc
from app.services.article_service import ArticleService
from app.auth import get_current_user, get_optional_user
from app.services.credit_service import credit_service, UsageAccumulator

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
    experiment_config_json = (
        req.experiment_config.model_dump_json() if req.experiment_config else None
    )
    project = await lab_service.create_project(
        db, req.title, req.description, req.topic,
        user_id=user_id, experiment_config_json=experiment_config_json,
    )
    return ResearchProjectResponse.model_validate(project)


@router.get("/projects/{project_id}")
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    detail = await lab_service.get_project_detail(db, project_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Project not found")
    return detail


@router.post("/projects/{project_id}/run-phase")
@limiter.limit("5/minute")
async def run_next_phase(request: Request, project_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db), auth_user: Optional[dict] = Depends(get_optional_user)):
    result = await db.execute(select(ResearchProject).where(ResearchProject.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.status == "completed":
        raise HTTPException(status_code=400, detail="Project already completed")
    if getattr(project, "phase_running", False):
        raise HTTPException(status_code=409, detail="A phase is already running")

    user_id = await _resolve_user_id(db, auth_user)
    if user_id:
        phase_name = project.current_phase or "hypothesis"
        est = credit_service.estimate_operation_cost(f"research_{phase_name}")
        check = await credit_service.check_credits(user_id, est, db)
        if not check["ok"]:
            raise HTTPException(402, detail={
                "error": "insufficient_credits",
                "balance": check["balance"],
                "required": check["required"],
                "message": "Not enough credits for this research phase.",
            })

    current_phase = project.current_phase

    async def _run(pid: int, uid: Optional[int]):
        acc = UsageAccumulator()
        token = _active_usage_acc.set(acc)
        try:
            async with async_session() as bg_db:
                await lab_service.run_next_phase(bg_db, pid)
                if uid and acc.billed_cost() > 0:
                    await credit_service.consume_credits(
                        uid, acc.billed_cost(), f"research_{current_phase}", bg_db,
                        resource_id=pid, details=acc.to_dict(),
                    )
        finally:
            _active_usage_acc.reset(token)

    background_tasks.add_task(_run, project_id, user_id)
    return {"message": f"Phase '{current_phase}' started in background", "phase": current_phase, "project_id": project_id}


@router.post("/projects/{project_id}/replay-phase")
@limiter.limit("5/minute")
async def replay_phase(request: Request, project_id: int, data: dict, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    phase = data.get("phase")
    if not phase:
        raise HTTPException(status_code=400, detail="Missing 'phase' in request body")
    result = await db.execute(select(ResearchProject).where(ResearchProject.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if getattr(project, "phase_running", False):
        raise HTTPException(status_code=409, detail="A phase is already running")

    async def _run(pid: int, ph: str):
        async with async_session() as bg_db:
            await lab_service.replay_phase(bg_db, pid, ph)

    background_tasks.add_task(_run, project_id, phase)
    return {"message": f"Replaying phase '{phase}' in background", "phase": phase, "project_id": project_id}


@router.post("/projects/{project_id}/run-all")
@limiter.limit("3/minute")
async def run_all_phases_endpoint(request: Request, project_id: int, background_tasks: BackgroundTasks):
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


@router.post("/projects/{project_id}/add-references")
@limiter.limit("5/minute")
async def add_more_references(request: Request, project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResearchProject).where(ResearchProject.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.topic:
        raise HTTPException(status_code=400, detail="Project has no topic for searching")
    before_count = await db.execute(
        select(func.count(ProjectReference.id)).where(ProjectReference.project_id == project_id)
    )
    before = before_count.scalar() or 0
    target = before + 10
    await lab_service._search_and_import_topic_papers(db, project, min_papers=target)
    after_count = await db.execute(
        select(func.count(ProjectReference.id)).where(ProjectReference.project_id == project_id)
    )
    after = after_count.scalar() or 0
    added = after - before
    return {"added": added, "total": after}


@router.get("/projects/{project_id}/environments")
async def get_project_environments(project_id: int, db: AsyncSession = Depends(get_db)):
    return await lab_service.get_project_environments(db, project_id)


@router.delete("/projects/{project_id}/environments/{env_id}")
async def delete_project_environment(project_id: int, env_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RLEnvironment).where(RLEnvironment.id == env_id, RLEnvironment.research_project_id == project_id)
    )
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found in this project")
    await db.execute(select(TrainingRun).where(TrainingRun.env_id == env_id))
    from sqlalchemy import delete as sql_delete
    await db.execute(sql_delete(TrainingRun).where(TrainingRun.env_id == env_id))
    await db.execute(sql_delete(EnvVersion).where(EnvVersion.env_id == env_id))
    await db.delete(env)
    await db.commit()
    return {"message": "Environment deleted"}


@router.get("/projects/{project_id}/training-runs")
async def get_project_training_runs(project_id: int, db: AsyncSession = Depends(get_db)):
    return await lab_service.get_project_training_runs(db, project_id)


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResearchProject).where(ResearchProject.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    from sqlalchemy import delete as sql_delete
    envs = await db.execute(select(RLEnvironment).where(RLEnvironment.research_project_id == project_id))
    for env in envs.scalars().all():
        await db.execute(sql_delete(TrainingRun).where(TrainingRun.env_id == env.id))
        await db.execute(sql_delete(EnvVersion).where(EnvVersion.env_id == env.id))
        await db.delete(env)
    await db.execute(sql_delete(AgentMessage).where(AgentMessage.project_id == project_id))
    await db.execute(sql_delete(AgentWork).where(AgentWork.project_id == project_id))
    await db.execute(sql_delete(ResearchPaper).where(ResearchPaper.project_id == project_id))
    await db.execute(sql_delete(ProjectReference).where(ProjectReference.project_id == project_id))
    await db.delete(project)
    await db.commit()
    return {"message": "Project deleted"}


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
@limiter.limit("3/minute")
async def paper_from_env(
    request: Request,
    env_id: int,
    background_tasks: BackgroundTasks,
    topic: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    auth_user: Optional[dict] = Depends(get_optional_user),
):
    user_id = await _resolve_user_id(db, auth_user)

    if user_id:
        est = credit_service.estimate_operation_cost("paper_from_env")
        check = await credit_service.check_credits(user_id, est, db)
        if not check["ok"]:
            raise HTTPException(402, detail={
                "error": "insufficient_credits",
                "balance": check["balance"],
                "required": check["required"],
                "message": "Not enough credits to generate a paper.",
            })

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
        acc = UsageAccumulator()
        token = _active_usage_acc.set(acc)
        try:
            async with async_session() as bg_db:
                await lab_service._paper_from_env_pipeline(bg_db, pid, eid, t, uid)
                if uid and acc.billed_cost() > 0:
                    await credit_service.consume_credits(
                        uid, acc.billed_cost(), "paper_from_env", bg_db,
                        resource_id=pid, details=acc.to_dict(),
                    )
        finally:
            _active_usage_acc.reset(token)

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

    figures = await _generate_inline_figures(db, project_id)

    paper_html = _inject_figures_into_paper(paper_html, figures)

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
tr:nth-child(even) {{ background: #fafafa; }}
.abstract {{ font-style: italic; margin: 16pt 20pt; padding: 12pt; background: #f9f9f9;
  border-left: 3px solid #666; }}
.figure {{ margin: 16pt 0; page-break-inside: avoid; }}
.figure img {{ max-width: 100%; height: auto; display: block; margin: 0 auto; }}
.figure-caption {{ text-align: center; font-size: 9pt; color: #555; margin-top: 4pt; font-style: italic; }}
.data-table {{ margin: 12pt 0; }}
.data-table caption {{ font-size: 9pt; color: #555; text-align: left; margin-bottom: 4pt; font-style: italic; }}
code {{ font-family: 'Courier New', monospace; font-size: 9pt; background: #f5f5f5; padding: 1px 4px; }}
pre {{ background: #f5f5f5; padding: 10px; border: 1px solid #ddd; overflow-x: auto; font-size: 9pt; }}
@media print {{
  body {{ padding: 0; }}
  .no-print {{ display: none; }}
  img {{ max-width: 100% !important; }}
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
</body>
</html>"""

    return HTMLResponse(content=html, headers={
        "Content-Disposition": f'inline; filename="{paper.title[:60].replace(chr(34), "")}.html"'
    })


def _inject_figures_into_paper(paper_html: str, figures: dict) -> str:
    """Inject charts, tables, and data into the paper HTML at relevant sections."""
    import re

    results_chart = figures.get("training_curves", "")
    results_table = figures.get("results_summary", "")
    eval_section = figures.get("eval_episodes", "")
    hyperparams = figures.get("hyperparameters", "")
    reproducibility = figures.get("reproducibility", "")

    section_patterns = [
        (r'(<h2[^>]*>.*?5\.?\s*Results.*?</h2>)', "after_results_heading"),
        (r'(<h3[^>]*>.*?5\.?1.*?Quantitative.*?</h3>)', "after_quantitative"),
        (r'(<h3[^>]*>.*?5\.?2.*?Learning.*?</h3>)', "after_learning"),
        (r'(<h2[^>]*>.*?4\.?\s*Experimental.*?</h2>)', "after_experimental"),
        (r'(<h2[^>]*>.*?3\.?\s*Methodology.*?</h2>)', "after_methodology"),
    ]

    injected = set()

    for pattern, section_id in section_patterns:
        match = re.search(pattern, paper_html, re.IGNORECASE)
        if not match:
            continue

        insert_pos = match.end()

        if section_id == "after_quantitative" and "results_table" not in injected and results_table:
            next_tag = re.search(r'<(h[23]|</body)', paper_html[insert_pos:])
            pos = insert_pos + next_tag.start() if next_tag else insert_pos + 200
            paper_html = paper_html[:pos] + results_table + paper_html[pos:]
            injected.add("results_table")
        elif section_id == "after_learning" and "curves" not in injected and results_chart:
            next_tag = re.search(r'<(h[23]|</body)', paper_html[insert_pos:])
            pos = insert_pos + next_tag.start() if next_tag else insert_pos + 200
            paper_html = paper_html[:pos] + results_chart + paper_html[pos:]
            injected.add("curves")
        elif section_id == "after_results_heading" and results_chart and "curves" not in injected:
            pass
        elif section_id == "after_experimental" and "hyperparams" not in injected and hyperparams:
            next_h2 = re.search(r'<h2', paper_html[insert_pos + 1:])
            pos = insert_pos + 1 + next_h2.start() if next_h2 else insert_pos + 500
            paper_html = paper_html[:pos] + hyperparams + reproducibility + paper_html[pos:]
            injected.add("hyperparams")

    if "curves" not in injected and results_chart:
        results_match = re.search(r'(<h2[^>]*>.*?5\.?\s*Results.*?</h2>)', paper_html, re.IGNORECASE)
        if results_match:
            next_h2 = re.search(r'<h2', paper_html[results_match.end() + 1:])
            pos = results_match.end() + 1 + next_h2.start() if next_h2 else len(paper_html) - 20
            paper_html = paper_html[:pos] + results_chart + results_table + eval_section + paper_html[pos:]
        else:
            paper_html += results_chart + results_table + eval_section

    if "results_table" not in injected and results_table and "curves" in injected:
        curves_pos = paper_html.find('class="figure-caption">Figure')
        if curves_pos > 0:
            end_div = paper_html.find('</div>', curves_pos)
            if end_div > 0:
                paper_html = paper_html[:end_div + 6] + results_table + paper_html[end_div + 6:]

    if "hyperparams" not in injected and hyperparams:
        paper_html += hyperparams + reproducibility

    if eval_section and "eval" not in injected:
        ref_match = re.search(r'(<h2[^>]*>.*?(?:Reference|Bibliograph).*?</h2>)', paper_html, re.IGNORECASE)
        if ref_match:
            paper_html = paper_html[:ref_match.start()] + eval_section + paper_html[ref_match.start():]
        else:
            paper_html += eval_section

    return paper_html


async def _generate_inline_figures(db: AsyncSession, project_id: int) -> dict:
    """Generate separate HTML fragments for inline injection into the paper."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import io, base64

    result = {"training_curves": "", "results_summary": "", "eval_episodes": "",
              "hyperparameters": "", "reproducibility": ""}

    env_ids_result = await db.execute(
        select(RLEnvironment.id, RLEnvironment.name).where(RLEnvironment.research_project_id == project_id)
    )
    env_map = {r[0]: r[1] for r in env_ids_result.fetchall()}
    if not env_map:
        return result

    runs_result = await db.execute(
        select(TrainingRun).where(
            TrainingRun.env_id.in_(list(env_map.keys())),
            TrainingRun.status == "completed",
        ).order_by(TrainingRun.created_at)
    )
    runs = runs_result.scalars().all()
    if not runs:
        return result

    fig_num = 1

    # ── Training Curves ─────────────────────────────────────────
    chart_runs = [(r, env_map.get(r.env_id, f"Env {r.env_id}")) for r in runs if r.training_curve_json]
    if chart_runs:
        curves_html = ""
        fig, ax = plt.subplots(figsize=(7, 3.5))
        for run, env_name in chart_runs:
            curve = json.loads(run.training_curve_json)
            rewards = [p.get("mean_reward", 0) for p in curve]
            steps = [p.get("timestep", i * 1000) for i, p in enumerate(curve)]
            ax.plot(steps, rewards, label=f"{env_name} ({run.algorithm})", linewidth=1.5)
        ax.set_xlabel("Training Steps", fontsize=10)
        ax.set_ylabel("Mean Reward", fontsize=10)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        curves_html += (
            f'<div class="figure">'
            f'<img src="data:image/png;base64,{base64.b64encode(buf.read()).decode()}" />'
            f'<p class="figure-caption">Figure {fig_num}. Training reward curves across all experiments.</p>'
            f'</div>'
        )
        fig_num += 1

        env_groups: dict[str, list] = {}
        for run, env_name in chart_runs:
            env_groups.setdefault(env_name, []).append(run)
        if len(env_groups) > 1:
            for env_name, env_runs in env_groups.items():
                fig, ax = plt.subplots(figsize=(6, 3))
                for run in env_runs:
                    curve = json.loads(run.training_curve_json)
                    rewards = [p.get("mean_reward", 0) for p in curve]
                    steps = [p.get("timestep", i * 1000) for i, p in enumerate(curve)]
                    ax.plot(steps, rewards, label=run.algorithm, linewidth=1.5)
                ax.set_xlabel("Training Steps", fontsize=9)
                ax.set_ylabel("Mean Reward", fontsize=9)
                ax.legend(fontsize=8)
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                buf = io.BytesIO()
                fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
                plt.close(fig)
                buf.seek(0)
                curves_html += (
                    f'<div class="figure">'
                    f'<img src="data:image/png;base64,{base64.b64encode(buf.read()).decode()}" />'
                    f'<p class="figure-caption">Figure {fig_num}. Learning dynamics for {env_name}.</p>'
                    f'</div>'
                )
                fig_num += 1
        result["training_curves"] = curves_html

    # ── Results Summary Table ───────────────────────────────────
    tbl = '<div class="data-table"><caption>Table 1. Quantitative training results.</caption>'
    tbl += '<table><thead><tr>'
    tbl += '<th>Environment</th><th>Algorithm</th><th>Mean Reward</th><th>&sigma;</th>'
    tbl += '<th>Success Rate</th><th>Ep. Length</th><th>Time</th><th>Steps</th>'
    tbl += '</tr></thead><tbody>'
    for run in runs:
        env_name = env_map.get(run.env_id, f"Env {run.env_id}")
        r = json.loads(run.results_json) if run.results_json else {}
        tbl += (f'<tr><td>{env_name}</td><td>{run.algorithm}</td>'
                f'<td>{r.get("mean_reward", "—")}</td><td>{r.get("std_reward", "—")}</td>'
                f'<td>{r.get("success_rate", "—")}</td><td>{r.get("mean_ep_length", "—")}</td>'
                f'<td>{r.get("training_time_sec", "—")}s</td><td>{r.get("total_timesteps", "—")}</td></tr>')
    tbl += '</tbody></table></div>'
    result["results_summary"] = tbl

    # ── Evaluation Episodes ─────────────────────────────────────
    eval_html = ""
    for run in runs:
        env_name = env_map.get(run.env_id, f"Env {run.env_id}")
        r = json.loads(run.results_json) if run.results_json else {}
        eval_rewards = r.get("eval_rewards", [])
        eval_lengths = r.get("eval_lengths", [])
        if not eval_rewards or len(eval_rewards) < 2:
            continue

        eval_html += f'<p><strong>{env_name} — {run.algorithm}</strong> ({len(eval_rewards)} eval episodes)</p>'
        eval_html += '<table><thead><tr><th>Episode</th><th>Reward</th><th>Length</th></tr></thead><tbody>'
        for ep_i, (rew, ln) in enumerate(zip(eval_rewards, eval_lengths or [None]*len(eval_rewards)), 1):
            eval_html += f'<tr><td>{ep_i}</td><td>{rew}</td><td>{ln if ln is not None else "—"}</td></tr>'
        eval_html += '</tbody></table>'

        if len(eval_rewards) >= 3:
            ncols = 2 if eval_lengths and all(v is not None for v in eval_lengths) else 1
            fig, axes = plt.subplots(1, ncols, figsize=(4 * ncols, 3))
            if ncols == 1:
                axes = [axes]
            else:
                axes = list(axes)
            axes[0].bar(range(1, len(eval_rewards)+1), eval_rewards, color="#4f86c6", alpha=0.8)
            axes[0].set_xlabel("Episode", fontsize=9)
            axes[0].set_ylabel("Reward", fontsize=9)
            axes[0].set_title(f"Eval Rewards", fontsize=10)
            axes[0].grid(True, alpha=0.3, axis="y")
            if ncols == 2:
                axes[1].bar(range(1, len(eval_lengths)+1), eval_lengths, color="#e8915a", alpha=0.8)
                axes[1].set_xlabel("Episode", fontsize=9)
                axes[1].set_ylabel("Steps", fontsize=9)
                axes[1].set_title("Episode Lengths", fontsize=10)
                axes[1].grid(True, alpha=0.3, axis="y")
            plt.tight_layout()
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)
            eval_html += (
                f'<div class="figure">'
                f'<img src="data:image/png;base64,{base64.b64encode(buf.read()).decode()}" />'
                f'<p class="figure-caption">Figure {fig_num}. Evaluation results for {env_name} ({run.algorithm}).</p>'
                f'</div>'
            )
            fig_num += 1
    result["eval_episodes"] = eval_html

    # ── Hyperparameters ─────────────────────────────────────────
    hp_html = '<h3>Hyperparameters</h3>'
    for run in runs:
        env_name = env_map.get(run.env_id, f"Env {run.env_id}")
        r = json.loads(run.results_json) if run.results_json else {}
        hyperparams = r.get("hyperparameters", {})
        cfg = json.loads(run.config_json) if run.config_json else {}
        all_params = {**cfg, **hyperparams}
        hp_html += f'<p style="font-size:10pt;"><strong>{env_name} — {run.algorithm}</strong></p>'
        hp_html += '<table><thead><tr><th>Parameter</th><th>Value</th></tr></thead><tbody>'
        skip = {"status", "model_path", "continue_from_path", "continue_from",
                "eval_rewards", "eval_lengths", "episodes_trained",
                "mean_reward", "std_reward", "success_rate",
                "mean_ep_length", "training_time_sec",
                "sb3_version", "gymnasium_version", "random_seed",
                "error", "traceback", "env_version", "curriculum"}
        priority = ["total_timesteps", "learning_rate", "gamma", "n_steps", "batch_size",
                     "n_epochs", "ent_coef", "vf_coef", "max_grad_norm", "gae_lambda"]
        shown = set()
        for k in priority:
            if k in all_params:
                hp_html += f'<tr><td><code>{k}</code></td><td>{all_params[k]}</td></tr>'
                shown.add(k)
        for k, v in all_params.items():
            if k not in shown and k not in skip:
                hp_html += f'<tr><td><code>{k}</code></td><td>{v}</td></tr>'
        hp_html += '</tbody></table>'
    result["hyperparameters"] = hp_html

    # ── Reproducibility ─────────────────────────────────────────
    repro = '<h3>Reproducibility</h3>'
    for run in runs:
        r = json.loads(run.results_json) if run.results_json else {}
        sb3 = r.get("sb3_version")
        gym = r.get("gymnasium_version")
        if sb3 or gym:
            repro += '<table><thead><tr><th>Component</th><th>Version</th></tr></thead><tbody>'
            repro += '<tr><td>Platform</td><td>Kualia AI Research Lab</td></tr>'
            if sb3: repro += f'<tr><td>Stable Baselines3</td><td>{sb3}</td></tr>'
            if gym: repro += f'<tr><td>Gymnasium</td><td>{gym}</td></tr>'
            repro += '<tr><td>Python</td><td>3.11+</td></tr></tbody></table>'
            break
    result["reproducibility"] = repro

    return result


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await lab_service.delete_project(db, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted"}
