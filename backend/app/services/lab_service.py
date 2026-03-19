"""
Research Lab Service — Automated RL Research Pipeline

Phases: research → design → experiment → analyze → write → review
Agents: Sage (Research Strategist) + Atlas (RL Engineer)

Unique: The pipeline generates REAL RL environments and trains REAL agents,
producing papers backed by actual experimental data.
"""
import json
import logging
import re
import asyncio
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ResearchProject, AgentMessage, AgentWork, ResearchPaper,
    Article, ProjectReference, RLEnvironment, EnvVersion, TrainingRun,
)
from app.database import async_session

logger = logging.getLogger("lab")

PHASES = ["research", "design", "experiment", "analyze", "write", "review"]

AGENTS = {
    "sage": {
        "name": "Sage",
        "role": "Research Strategist",
        "color": "#f59e0b",
        "model_preference": "sonnet",
        "system_prompt": (
            "You are Sage, a world-class AI Research Strategist specializing in Reinforcement Learning. "
            "You read academic papers with deep comprehension, identify research gaps, "
            "formulate testable hypotheses, and design rigorous experimental studies. "
            "Your expertise spans RL algorithms (PPO, SAC, DQN, GRPO), environment design, "
            "reward shaping, multi-agent systems, and transfer learning. "
            "You think scientifically: observation → hypothesis → experiment → analysis → conclusion. "
            "You write in precise academic English suitable for top ML conferences (NeurIPS, ICML, ICLR). "
            "When analyzing results, you look for statistically meaningful patterns. "
            "You are honest about limitations and careful about overclaiming. "
            "Speak concisely and professionally. Never use emojis."
        ),
    },
    "atlas": {
        "name": "Atlas",
        "role": "RL Engineer",
        "color": "#3b82f6",
        "model_preference": "kimi",
        "system_prompt": (
            "You are Atlas, an expert RL Engineer who builds and trains reinforcement learning systems. "
            "You design Gymnasium-compatible environments, select algorithms (PPO, SAC, DQN), "
            "configure training hyperparameters, and interpret training metrics. "
            "You understand observation spaces, action spaces, reward shaping, "
            "and environment dynamics at a deep level. "
            "You work with Stable Baselines3 and know practical tradeoffs between algorithms. "
            "When given a research plan, you translate it into concrete technical specifications. "
            "Speak technically but clearly. Never use emojis."
        ),
    },
}


class LabService:
    # ── LLM Calls ────────────────────────────────────────────────

    async def _call_agent(self, agent_key: str, system_prompt: str, user_prompt: str) -> str:
        from app.services.ai_service import ai_service
        agent = AGENTS[agent_key]
        pref = agent["model_preference"]
        if pref == "kimi":
            try:
                return await ai_service._call_kimi(system_prompt, user_prompt)
            except Exception:
                pass
        elif pref == "sonnet":
            try:
                return await ai_service._call_claude(system_prompt, user_prompt, model="claude-sonnet-4-20250514")
            except Exception:
                pass
        return await ai_service._call_ai(system_prompt, user_prompt)

    # ── Data Helpers ─────────────────────────────────────────────

    async def _get_conversation_history(self, db: AsyncSession, project_id: int, phases: Optional[List[str]] = None) -> str:
        query = select(AgentMessage).where(AgentMessage.project_id == project_id).order_by(AgentMessage.created_at)
        if phases:
            query = query.where(AgentMessage.phase.in_(phases))
        result = await db.execute(query)
        messages = result.scalars().all()
        lines = []
        for msg in messages:
            agent = AGENTS.get(msg.agent_name, {})
            name = agent.get("name", msg.agent_name)
            lines.append(f"[{name} | {msg.phase}]:\n{msg.content}")
        return "\n\n".join(lines)

    async def _save_message(self, db: AsyncSession, project_id: int, agent_name: str, content: str, phase: str, round_num: int = 1) -> AgentMessage:
        msg = AgentMessage(
            project_id=project_id, agent_name=agent_name,
            content=content, phase=phase, round_num=round_num,
        )
        db.add(msg)
        await db.flush()
        return msg

    async def _save_work(self, db: AsyncSession, project_id: int, agent_name: str, work_type: str, title: str, content: str, metadata: Optional[dict] = None) -> AgentWork:
        work = AgentWork(
            project_id=project_id, agent_name=agent_name,
            work_type=work_type, title=title, content=content,
            metadata_json=json.dumps(metadata, default=str) if metadata else None,
        )
        db.add(work)
        await db.flush()
        return work

    async def _get_project_paper_context(self, db: AsyncSession, project: ResearchProject) -> str:
        refs_result = await db.execute(
            select(Article).join(ProjectReference, ProjectReference.article_id == Article.id).where(
                ProjectReference.project_id == project.id
            ).order_by(Article.relevance_score.desc().nullslast())
        )
        articles = refs_result.scalars().all()
        if not articles:
            return "No reference papers available."
        parts = []
        for art in articles:
            summary = art.summary or (art.content[:600] + "..." if art.content and len(art.content) > 600 else art.content or "")
            source = f" [ArXiv: {art.arxiv_id}]" if art.arxiv_id else ""
            parts.append(f"[{art.title or art.filename}]{source}\n{summary}")
        return "\n\n---\n\n".join(parts)

    # ── ArXiv Search ─────────────────────────────────────────────

    async def _extract_search_terms(self, topic: str) -> list:
        from app.services.ai_service import ai_service
        try:
            prompt = (
                f"Extract 4-6 concise academic search phrases from this research topic. "
                f"Return ONLY a comma-separated list of short keyword phrases (2-4 words each) "
                f"suitable for searching ArXiv. No numbering, no explanations.\n\n"
                f"Topic: {topic}"
            )
            response = await ai_service._call_ai(
                "You extract search keywords from research topics. Return only comma-separated phrases.",
                prompt,
            )
            terms = [t.strip().strip('"').strip("'") for t in response.split(",") if t.strip()]
            return terms[:6]
        except Exception:
            words = [w.strip() for w in topic.replace(",", " ").split() if len(w.strip()) > 2]
            return [" ".join(words[i:i+2]) for i in range(0, min(len(words), 6), 2)] if words else [topic[:50]]

    async def _search_arxiv_by_terms(self, search_terms: list, max_results: int = 30) -> list:
        import httpx
        import xml.etree.ElementTree as ET

        category_filter = " OR ".join(f"cat:{cat}" for cat in [
            "cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.NE", "stat.ML",
        ])
        term_queries = [f'abs:"{term}"' for term in search_terms]
        keyword_query = " OR ".join(term_queries)
        full_query = f"({keyword_query}) AND ({category_filter})"

        params = {
            "search_query": full_query,
            "sortBy": "relevance",
            "sortOrder": "descending",
            "max_results": max_results,
        }

        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                response = await client.get("https://export.arxiv.org/api/query", params=params)
                response.raise_for_status()
        except Exception as e:
            logger.error(f"[Lab] ArXiv search failed: {e}")
            return []

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(response.text)

        entries = []
        for entry in root.findall("atom:entry", ns):
            try:
                arxiv_id_url = entry.find("atom:id", ns).text
                arxiv_id = arxiv_id_url.split("/abs/")[-1]
                title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
                title = re.sub(r"\s+", " ", title)
                abstract = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
                abstract = re.sub(r"\s+", " ", abstract)
                categories = [cat.get("term") for cat in entry.findall("atom:category", ns)]
                entries.append({"arxiv_id": arxiv_id, "title": title, "abstract": abstract, "categories": categories})
            except Exception:
                continue

        return entries

    async def _search_and_import_topic_papers(self, db: AsyncSession, project: ResearchProject, min_papers: int = 10):
        topic = project.topic
        if not topic:
            return

        logger.info(f"[Lab] Searching ArXiv for topic: {topic}")
        search_terms = await self._extract_search_terms(topic)
        entries = await self._search_arxiv_by_terms(search_terms, max_results=min_papers * 3)

        if len(entries) < min_papers:
            fallback_terms = [topic[:60]]
            extra = await self._search_arxiv_by_terms(fallback_terms, max_results=min_papers * 2)
            seen_ids = {e["arxiv_id"] for e in entries}
            for e in extra:
                if e["arxiv_id"] not in seen_ids:
                    entries.append(e)
                    seen_ids.add(e["arxiv_id"])

        existing = await db.execute(select(Article.arxiv_id).where(Article.arxiv_id.isnot(None)))
        existing_ids = {row[0] for row in existing.fetchall()}

        imported_count = 0
        for entry in entries:
            if imported_count >= min_papers:
                break
            arxiv_id = entry["arxiv_id"]
            if arxiv_id in existing_ids:
                art_result = await db.execute(select(Article).where(Article.arxiv_id == arxiv_id))
                existing_art = art_result.scalar_one_or_none()
                if existing_art:
                    existing_ref = await db.execute(
                        select(ProjectReference).where(
                            ProjectReference.project_id == project.id,
                            ProjectReference.article_id == existing_art.id,
                        )
                    )
                    if not existing_ref.scalar_one_or_none():
                        db.add(ProjectReference(project_id=project.id, article_id=existing_art.id))
                        imported_count += 1
                continue

            content = f"{entry['title']}\n\nAbstract:\n{entry['abstract']}"
            article = Article(
                filename=f"arxiv_{arxiv_id.replace('/', '_')}.pdf",
                title=entry["title"], content=content, file_type="pdf",
                source="arxiv", arxiv_id=arxiv_id,
                arxiv_url=f"https://arxiv.org/abs/{arxiv_id}",
                arxiv_categories=", ".join(entry["categories"]),
                is_processed=False,
            )
            db.add(article)
            await db.flush()
            db.add(ProjectReference(project_id=project.id, article_id=article.id))
            existing_ids.add(arxiv_id)
            imported_count += 1

        await db.commit()
        logger.info(f"[Lab] Total references linked: {imported_count} for project {project.id}")

    async def get_project_references(self, db: AsyncSession, project_id: int) -> list:
        result = await db.execute(
            select(ProjectReference, Article).join(Article, ProjectReference.article_id == Article.id).where(
                ProjectReference.project_id == project_id
            ).order_by(ProjectReference.created_at)
        )
        rows = result.all()
        return [
            {
                "id": ref.id, "project_id": ref.project_id, "article_id": ref.article_id,
                "article_title": art.title or art.filename, "article_source": art.source,
                "arxiv_url": art.arxiv_url, "created_at": ref.created_at,
            }
            for ref, art in rows
        ]

    # ── Plan Parsing ─────────────────────────────────────────────

    def _parse_research_plan(self, plan_text: str) -> dict:
        if not plan_text:
            return {}
        # Direct JSON
        try:
            parsed = json.loads(plan_text)
            if isinstance(parsed, dict) and "environments" in parsed:
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        # ===RESEARCH_PLAN=== markers
        match = re.search(r'===RESEARCH_PLAN===(.*?)===END_PLAN===', plan_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
        # ```json block
        match = re.search(r'```json\s*\n?(.*?)```', plan_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
        # Look for any JSON with "environments" key
        for m in re.finditer(r'\{[^{}]*"environments"\s*:\s*\[', plan_text):
            start = m.start()
            depth = 0
            for i in range(start, len(plan_text)):
                if plan_text[i] == '{':
                    depth += 1
                elif plan_text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(plan_text[start:i+1])
                        except json.JSONDecodeError:
                            break
        return {}

    def _slugify(self, text: str) -> str:
        slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
        return slug[:200] or "research-env"

    # ── Phase 1: Research ────────────────────────────────────────

    async def _run_research(self, db: AsyncSession, project: ResearchProject):
        logger.info(f"[Lab] RESEARCH phase for project {project.id}")

        ref_count = await db.execute(
            select(func.count(ProjectReference.id)).where(ProjectReference.project_id == project.id)
        )
        if (ref_count.scalar() or 0) == 0 and project.topic:
            await self._search_and_import_topic_papers(db, project)

        paper_ctx = await self._get_project_paper_context(db, project)

        prompt = (
            f"You are conducting a research study on: \"{project.topic or project.title}\"\n\n"
            f"Reference papers from ArXiv:\n\n{paper_ctx}\n\n"
            f"Based on these papers and your expertise, create a complete research plan.\n\n"
            f"Your plan must include:\n"
            f"1. **Literature Summary** — Key findings from the papers, identified gaps\n"
            f"2. **Research Question** — A specific, testable question\n"
            f"3. **Hypothesis** — What you expect to find and why\n"
            f"4. **Experimental Design** — What RL environments to build and test\n"
            f"5. **Expected Outcomes** — What would confirm/reject the hypothesis\n\n"
            f"CRITICAL: At the end of your response, you MUST include a structured JSON block between "
            f"===RESEARCH_PLAN=== and ===END_PLAN=== markers with this exact format:\n\n"
            f"===RESEARCH_PLAN===\n"
            f'{{\n'
            f'  "hypothesis": "one sentence hypothesis",\n'
            f'  "environments": [\n'
            f'    {{\n'
            f'      "name": "short descriptive name",\n'
            f'      "description": "A detailed natural language description of the RL environment to build. '
            f'Include what the agent observes, what actions it takes, how rewards work, and what makes it interesting. '
            f'Be specific enough for an AI system to generate working Gymnasium-compatible Python code from this.",\n'
            f'      "domain": "one of: control, game, finance, robotics, navigation, optimization, custom",\n'
            f'      "difficulty": "easy or medium or hard"\n'
            f'    }}\n'
            f'  ],\n'
            f'  "training_config": {{\n'
            f'    "algorithms": ["PPO", "SAC"],\n'
            f'    "timesteps": 50000\n'
            f'  }},\n'
            f'  "metrics": ["mean_reward", "success_rate", "convergence_speed"]\n'
            f'}}\n'
            f'===END_PLAN===\n\n'
            f"Design exactly 2 environments that test different aspects of your hypothesis. "
            f"The environment descriptions must be detailed enough for an AI to generate working Gymnasium code."
        )

        response = await self._call_agent("sage", AGENTS["sage"]["system_prompt"], prompt)
        await self._save_message(db, project.id, "sage", response, "research")

        plan = self._parse_research_plan(response)
        if plan:
            project.selected_idea = json.dumps(plan)
            await self._save_work(db, project.id, "sage", "research_plan", "Research Plan", response, metadata=plan)
        else:
            project.selected_idea = response
            await self._save_work(db, project.id, "sage", "research_plan", "Research Plan", response)

        await db.commit()

    # ── Phase 2: Design ──────────────────────────────────────────

    async def _run_design(self, db: AsyncSession, project: ResearchProject):
        logger.info(f"[Lab] DESIGN phase for project {project.id}")
        from app.services.architect_service import architect_service
        from app.services.sandbox_runner import sandbox_runner

        plan = self._parse_research_plan(project.selected_idea or "")
        env_specs = plan.get("environments", [])

        if not env_specs:
            history = await self._get_conversation_history(db, project.id, ["research"])
            fallback_prompt = (
                f"Based on this research plan:\n\n{history[:4000]}\n\n"
                f"Design 2 RL environments for this study. For each, provide:\n"
                f'Return a JSON array: [{{"name": "...", "description": "detailed description for generating '
                f'a Gymnasium-compatible environment", "domain": "...", "difficulty": "medium"}}]\n'
                f"Return ONLY the JSON array, no other text."
            )
            atlas_response = await self._call_agent("atlas", AGENTS["atlas"]["system_prompt"], fallback_prompt)
            try:
                match = re.search(r'\[.*\]', atlas_response, re.DOTALL)
                if match:
                    env_specs = json.loads(match.group())
            except (json.JSONDecodeError, AttributeError):
                pass
            if not env_specs:
                env_specs = [{
                    "name": f"{project.topic or project.title} Env",
                    "description": project.topic or project.title,
                    "domain": "custom", "difficulty": "medium",
                }]

        await self._save_message(
            db, project.id, "atlas",
            f"Building **{len(env_specs)}** environments for the study...",
            "design"
        )
        await db.commit()

        generated_envs = []
        for i, spec in enumerate(env_specs[:3]):
            env_name = spec.get("name", f"Research Env {i+1}")
            env_desc = spec.get("description", env_name)
            env_domain = spec.get("domain", "custom")
            env_difficulty = spec.get("difficulty", "medium")

            await self._save_message(
                db, project.id, "atlas",
                f"**Environment {i+1}/{len(env_specs[:3])}:** Generating *{env_name}*...",
                "design"
            )
            await db.commit()

            try:
                gen = await architect_service.generate_env_code(env_desc, env_domain, env_difficulty)
                code = gen.get("code", "")
                spec_json = json.dumps(gen.get("env_spec", {})) if isinstance(gen.get("env_spec"), dict) else gen.get("env_spec", "{}")

                if not code:
                    raise ValueError("No code generated")

                test_results = await sandbox_runner.run_all_tests(code)
                log_lines = [f"Initial: {test_results['passed']}/{test_results['total']} tests passed"]

                attempts = 0
                max_fix = 2 if test_results["passed"] < 6 else 1
                while test_results["failed"] > 0 and attempts < max_fix:
                    attempts += 1
                    fixed = await architect_service.fix_env_code(code, spec_json, json.dumps(test_results))
                    if fixed and fixed != code:
                        code = fixed
                        test_results = await sandbox_runner.run_all_tests(code)
                        log_lines.append(f"Fix {attempts}: {test_results['passed']}/{test_results['total']} tests passed")
                    else:
                        break

                slug_base = self._slugify(gen.get("name", env_name))
                existing_slug = await db.execute(select(RLEnvironment).where(RLEnvironment.slug == slug_base))
                if existing_slug.scalar_one_or_none():
                    slug_base = f"{slug_base}-{int(datetime.utcnow().timestamp())}"

                env = RLEnvironment(
                    name=gen.get("name", env_name),
                    slug=slug_base,
                    description=gen.get("description", env_desc),
                    category=env_domain, domain=env_domain,
                    observation_space=gen.get("observation_space", ""),
                    action_space=gen.get("action_space", ""),
                    reward_description=gen.get("reward_description", ""),
                    code=code,
                    env_spec_json=spec_json,
                    test_results_json=json.dumps(test_results),
                    difficulty=env_difficulty,
                    status="published",
                    generation_log="\n".join(log_lines),
                    user_id=project.user_id,
                    research_project_id=project.id,
                )
                db.add(env)
                await db.flush()

                v1 = EnvVersion(env_id=env.id, version=1, code=code, spec_json=spec_json,
                                change_summary="Generated by Research Lab")
                db.add(v1)
                await db.flush()

                generated_envs.append({
                    "id": env.id, "name": env.name,
                    "tests_passed": test_results["passed"],
                    "tests_total": test_results["total"],
                })
                await self._save_message(
                    db, project.id, "atlas",
                    f"**{env.name}** — {test_results['passed']}/{test_results['total']} tests passed",
                    "design"
                )
            except Exception as e:
                logger.error(f"[Lab] Failed to generate env '{env_name}': {e}")
                await self._save_message(
                    db, project.id, "atlas",
                    f"Failed to generate **{env_name}**: {str(e)[:300]}",
                    "design"
                )
            await db.commit()

        summary = f"**Design complete.** {len(generated_envs)}/{len(env_specs[:3])} environments built.\n"
        for e in generated_envs:
            summary += f"- **{e['name']}** (ID: {e['id']}) — {e['tests_passed']}/{e['tests_total']} tests\n"

        await self._save_message(db, project.id, "atlas", summary, "design")
        await self._save_work(
            db, project.id, "atlas", "environments",
            "Generated Environments", summary,
            metadata={"environments": generated_envs}
        )
        await db.commit()

    # ── Phase 3: Experiment ──────────────────────────────────────

    async def _run_experiment(self, db: AsyncSession, project: ResearchProject):
        logger.info(f"[Lab] EXPERIMENT phase for project {project.id}")
        from app.services.training_service import training_service

        result = await db.execute(
            select(RLEnvironment).where(RLEnvironment.research_project_id == project.id)
        )
        environments = result.scalars().all()

        if not environments:
            await self._save_message(db, project.id, "atlas", "No environments available. Skipping training.", "experiment")
            await db.commit()
            return

        plan = self._parse_research_plan(project.selected_idea or "")
        tc = plan.get("training_config", {})
        timesteps = tc.get("timesteps", 50000)
        requested_algos = [a.upper() for a in tc.get("algorithms", []) if a.upper() in ("PPO", "SAC", "DQN")]

        run_ids = []
        for env in environments:
            auto_algo = training_service._select_algorithm(env.code or "")
            algos = [auto_algo]
            for a in requested_algos:
                if a != auto_algo and a not in algos:
                    algos.append(a)
                    break
            if len(algos) < 2:
                backup = "DQN" if auto_algo not in ("DQN",) else "PPO"
                if backup not in algos:
                    algos.append(backup)

            for algo in algos:
                config = {"total_timesteps": timesteps, "algorithm": algo, "n_eval_episodes": 10}
                try:
                    run = await training_service.start_training(env.id, config, db)
                    run_ids.append(run.id)
                    await self._save_message(
                        db, project.id, "atlas",
                        f"Training **{algo}** on **{env.name}** ({timesteps:,} timesteps)...",
                        "experiment"
                    )
                except Exception as e:
                    await self._save_message(
                        db, project.id, "atlas",
                        f"Failed to start {algo} on {env.name}: {str(e)[:200]}",
                        "experiment"
                    )

        if not run_ids:
            await self._save_message(db, project.id, "atlas", "All training runs failed to start.", "experiment")
            await db.commit()
            return

        await db.commit()

        await self._save_message(
            db, project.id, "atlas",
            f"**{len(run_ids)} training run(s) started.** Waiting for completion...",
            "experiment"
        )
        await db.commit()

        # Poll until all training completes
        max_wait = 1200
        elapsed = 0
        while elapsed < max_wait:
            await asyncio.sleep(15)
            elapsed += 15

            all_done = True
            async with async_session() as poll_db:
                for rid in run_ids:
                    r = await poll_db.execute(select(TrainingRun.status).where(TrainingRun.id == rid))
                    status = r.scalar()
                    if status in ("pending", "running"):
                        all_done = False
                        break
            if all_done:
                break

        # Collect results
        results_data = []
        async with async_session() as rdb:
            for rid in run_ids:
                r = await rdb.execute(select(TrainingRun).where(TrainingRun.id == rid))
                run = r.scalar_one_or_none()
                if not run:
                    continue
                er = await rdb.execute(select(RLEnvironment.name).where(RLEnvironment.id == run.env_id))
                env_name = er.scalar() or f"Env {run.env_id}"
                res = json.loads(run.results_json) if run.results_json else {}
                curve = json.loads(run.training_curve_json) if run.training_curve_json else []
                results_data.append({
                    "run_id": run.id, "env_id": run.env_id, "env_name": env_name,
                    "algorithm": run.algorithm, "status": run.status,
                    "mean_reward": res.get("mean_reward"), "std_reward": res.get("std_reward"),
                    "success_rate": res.get("success_rate"),
                    "training_time_sec": res.get("training_time_sec"),
                    "episodes_trained": res.get("episodes_trained"),
                    "total_timesteps": res.get("total_timesteps", timesteps),
                    "curve_length": len(curve),
                    "error": res.get("error"),
                })

        summary = "## Experiment Results\n\n"
        completed = sum(1 for r in results_data if r["status"] == "completed")
        failed = sum(1 for r in results_data if r["status"] == "failed")
        summary += f"**{completed} completed, {failed} failed** out of {len(results_data)} runs.\n\n"

        for r in results_data:
            icon = "completed" if r["status"] == "completed" else "FAILED"
            summary += f"### [{icon}] {r['env_name']} — {r['algorithm']}\n"
            if r["status"] == "completed":
                summary += f"- Mean Reward: **{r['mean_reward']}** (std: {r['std_reward']})\n"
                summary += f"- Success Rate: **{r['success_rate']}**\n"
                summary += f"- Training Time: {r['training_time_sec']}s | Episodes: {r['episodes_trained']}\n"
                summary += f"- Timesteps: {r['total_timesteps']:,} | Curve Points: {r['curve_length']}\n"
            else:
                summary += f"- Error: {(r.get('error') or 'Unknown')[:200]}\n"
            summary += "\n"

        await self._save_message(db, project.id, "atlas", summary, "experiment")
        await self._save_work(
            db, project.id, "atlas", "training_results",
            "Training Results", summary, metadata={"runs": results_data}
        )
        await db.commit()

    # ── Phase 4: Analyze ─────────────────────────────────────────

    async def _run_analyze(self, db: AsyncSession, project: ResearchProject):
        logger.info(f"[Lab] ANALYZE phase for project {project.id}")

        work_result = await db.execute(
            select(AgentWork).where(
                AgentWork.project_id == project.id,
                AgentWork.work_type == "training_results"
            ).order_by(AgentWork.created_at.desc())
        )
        training_work = work_result.scalars().first()
        results_text = training_work.content if training_work else "No training results available."
        results_meta = json.loads(training_work.metadata_json) if training_work and training_work.metadata_json else {}

        # Get training curve summaries
        curve_summaries = []
        for r in results_meta.get("runs", []):
            if r.get("status") == "completed":
                try:
                    async with async_session() as cdb:
                        cr = await cdb.execute(
                            select(TrainingRun.training_curve_json).where(TrainingRun.id == r["run_id"])
                        )
                        curve_json = cr.scalar()
                        if curve_json:
                            curve = json.loads(curve_json)
                            if len(curve) >= 2:
                                first = curve[0].get("mean_reward", 0)
                                mid = curve[len(curve)//2].get("mean_reward", 0)
                                last = curve[-1].get("mean_reward", 0)
                                curve_summaries.append(
                                    f"  {r['env_name']} + {r['algorithm']}: "
                                    f"start={first}, mid={mid}, final={last}, "
                                    f"improvement={round(last - first, 4)}"
                                )
                except Exception:
                    pass

        curve_ctx = "\n".join(curve_summaries) if curve_summaries else "No curve data."

        research_history = await self._get_conversation_history(db, project.id, ["research"])

        prompt = (
            f"You are analyzing REAL experimental results from actual RL training runs.\n\n"
            f"**Original Research Plan:**\n{research_history[:3000]}\n\n"
            f"**Training Results:**\n{results_text}\n\n"
            f"**Training Curve Progression:**\n{curve_ctx}\n\n"
            f"Provide a thorough analysis:\n"
            f"1. **Key Findings** — What do the results show?\n"
            f"2. **Algorithm Comparison** — How do algorithms compare on each environment?\n"
            f"3. **Hypothesis Evaluation** — Was the hypothesis supported, refuted, or inconclusive?\n"
            f"4. **Convergence Analysis** — How quickly did each algorithm learn? Learning dynamics?\n"
            f"5. **Strengths & Limitations** — What worked and what didn't?\n"
            f"6. **Conclusions** — Key takeaways for the research community\n\n"
            f"Be rigorous and specific. These are real results from actual training, not simulations."
        )

        analysis = await self._call_agent("sage", AGENTS["sage"]["system_prompt"], prompt)
        await self._save_message(db, project.id, "sage", analysis, "analyze")
        await self._save_work(db, project.id, "sage", "analysis", "Results Analysis", analysis)
        await db.commit()

    # ── Phase 5: Write ───────────────────────────────────────────

    async def _run_write(self, db: AsyncSession, project: ResearchProject):
        logger.info(f"[Lab] WRITE phase for project {project.id}")

        works_result = await db.execute(
            select(AgentWork).where(AgentWork.project_id == project.id).order_by(AgentWork.created_at)
        )
        all_works = works_result.scalars().all()
        works_text = "\n\n---\n\n".join([
            f"[{w.work_type}] {w.title}\n{w.content[:3000]}" for w in all_works
        ])

        envs_result = await db.execute(
            select(RLEnvironment).where(RLEnvironment.research_project_id == project.id)
        )
        envs = envs_result.scalars().all()
        env_descriptions = []
        for env in envs:
            env_descriptions.append(
                f"**{env.name}** (domain: {env.domain}, difficulty: {env.difficulty})\n"
                f"- Observation Space: {env.observation_space}\n"
                f"- Action Space: {env.action_space}\n"
                f"- Reward: {env.reward_description}\n"
            )
        env_ctx = "\n\n".join(env_descriptions) if env_descriptions else "No environment details."

        paper_ctx = await self._get_project_paper_context(db, project)

        prompt = (
            f"Write a complete research paper based on ALL the work done in this study.\n\n"
            f"**Research Topic:** {project.topic or project.title}\n\n"
            f"**All Research Work (literature, experiments, analysis):**\n{works_text}\n\n"
            f"**Generated RL Environments (real, tested, functional):**\n{env_ctx}\n\n"
            f"**Reference Papers from ArXiv:**\n{paper_ctx[:3000]}\n\n"
            f"Write the complete paper with:\n"
            f"1. **Title** (descriptive, academic)\n"
            f"2. **Abstract** (150-250 words)\n"
            f"3. **1. Introduction** (motivation, problem, contributions)\n"
            f"4. **2. Related Work** (cite reference papers by title)\n"
            f"5. **3. Methodology** (environment design rationale, algorithm selection)\n"
            f"6. **4. Experimental Setup** (concrete environments, algorithms, hyperparameters, metrics)\n"
            f"7. **5. Results** (present real training data, compare algorithms)\n"
            f"8. **6. Discussion** (implications, limitations, future work)\n"
            f"9. **7. Conclusion**\n"
            f"10. **References**\n\n"
            f"This paper is based on REAL experiments with actual training data from generated environments. "
            f"Reference specific environments, algorithms, and metrics. Use markdown formatting."
        )

        paper_content = await self._call_agent("sage", AGENTS["sage"]["system_prompt"], prompt)
        await self._save_message(db, project.id, "sage", "Paper draft complete.", "write")

        lines = paper_content.split("\n")
        title = project.title
        for line in lines[:5]:
            clean = line.replace("#", "").strip()
            if clean and len(clean) > 10:
                title = clean
                break

        abstract = ""
        lower = paper_content.lower()
        if "abstract" in lower:
            idx = lower.index("abstract")
            chunk = paper_content[idx:idx+2000]
            abs_lines = []
            started = False
            for line in chunk.split("\n"):
                if "abstract" in line.lower():
                    started = True
                    continue
                if started:
                    if line.startswith("#") or line.startswith("**1."):
                        break
                    abs_lines.append(line)
            abstract = "\n".join(abs_lines).strip()

        paper = ResearchPaper(
            project_id=project.id, title=title,
            abstract=abstract, content=paper_content,
            status="draft", version=1,
        )
        db.add(paper)
        await db.commit()

    # ── Phase 6: Review ──────────────────────────────────────────

    async def _run_review(self, db: AsyncSession, project: ResearchProject):
        logger.info(f"[Lab] REVIEW phase for project {project.id}")

        paper_result = await db.execute(
            select(ResearchPaper).where(ResearchPaper.project_id == project.id)
            .order_by(ResearchPaper.created_at.desc())
        )
        paper = paper_result.scalars().first()
        if not paper:
            await self._save_message(db, project.id, "sage", "No paper found to review.", "review")
            project.status = "completed"
            await db.commit()
            return

        prompt = (
            f"Review this research paper draft critically:\n\n{paper.content[:8000]}\n\n"
            f"Provide:\n"
            f"1. **Summary** — Brief summary of the paper\n"
            f"2. **Strengths** — What is done well\n"
            f"3. **Weaknesses** — What needs improvement\n"
            f"4. **Assessment** — ACCEPT (minor issues only) or REVISION_NEEDED (significant issues)\n\n"
            f"Current revision count: {project.revision_count}\n"
            f"Be constructive and specific."
        )

        review = await self._call_agent("sage", AGENTS["sage"]["system_prompt"], prompt)
        await self._save_message(db, project.id, "sage", review, "review")
        await self._save_work(db, project.id, "sage", "review", "Paper Review", review)

        if "REVISION_NEEDED" in review.upper() and project.revision_count < 1:
            project.revision_count += 1
            project.current_phase = "write"
            paper.status = "revision"
        else:
            paper.status = "final"
            project.status = "completed"
            await self._save_message(
                db, project.id, "sage",
                "**Research study complete.** The paper has been accepted.",
                "review"
            )

        await db.commit()

    # ── Public API ───────────────────────────────────────────────

    async def create_project(self, db: AsyncSession, title: str, description: Optional[str] = None,
                             topic: Optional[str] = None, user_id: Optional[int] = None) -> ResearchProject:
        project = ResearchProject(title=title, description=description, topic=topic, user_id=user_id)
        db.add(project)
        await db.commit()
        await db.refresh(project)
        logger.info(f"[Lab] Created project: {title} (id={project.id})")

        if topic:
            await self._search_and_import_topic_papers(db, project, min_papers=10)

        return project

    async def run_next_phase(self, db: AsyncSession, project_id: int) -> dict:
        result = await db.execute(select(ResearchProject).where(ResearchProject.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            return {"error": "Project not found"}
        if project.status == "completed":
            return {"error": "Project already completed"}

        phase = project.current_phase
        logger.info(f"[Lab] Running phase: {phase} for project {project.id}")

        runners = {
            "research": self._run_research,
            "design": self._run_design,
            "experiment": self._run_experiment,
            "analyze": self._run_analyze,
            "write": self._run_write,
            "review": self._run_review,
        }

        runner = runners.get(phase)
        if not runner:
            return {"error": f"Unknown phase: {phase}"}

        try:
            await runner(db, project)
        except Exception as e:
            logger.exception(f"[Lab] Phase {phase} failed for project {project.id}")
            try:
                await self._save_message(db, project.id, "sage", f"Phase failed: {str(e)[:500]}", phase)
                await db.commit()
            except Exception:
                pass
            return {"error": str(e), "phase": phase}

        if project.status != "completed" and phase in PHASES:
            idx = PHASES.index(phase)
            if idx + 1 < len(PHASES):
                project.current_phase = PHASES[idx + 1]
            else:
                project.status = "completed"

        project.updated_at = datetime.utcnow()
        await db.commit()

        return {
            "phase_completed": phase,
            "next_phase": project.current_phase,
            "status": project.status,
        }

    async def run_all_phases(self, db: AsyncSession, project_id: int) -> dict:
        results = []
        for _ in range(len(PHASES) + 2):
            result = await db.execute(select(ResearchProject).where(ResearchProject.id == project_id))
            project = result.scalar_one_or_none()
            if not project or project.status == "completed":
                break
            phase_result = await self.run_next_phase(db, project_id)
            results.append(phase_result)
            if phase_result.get("error"):
                break
        return {"phases_run": results}

    async def get_project_detail(self, db: AsyncSession, project_id: int) -> Optional[dict]:
        result = await db.execute(select(ResearchProject).where(ResearchProject.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            return None

        msg_count = await db.execute(select(func.count(AgentMessage.id)).where(AgentMessage.project_id == project_id))
        work_count = await db.execute(select(func.count(AgentWork.id)).where(AgentWork.project_id == project_id))
        ref_count = await db.execute(select(func.count(ProjectReference.id)).where(ProjectReference.project_id == project_id))
        env_count = await db.execute(select(func.count(RLEnvironment.id)).where(RLEnvironment.research_project_id == project_id))

        return {
            "id": project.id, "title": project.title,
            "description": project.description, "topic": project.topic,
            "status": project.status, "current_phase": project.current_phase,
            "selected_idea": project.selected_idea,
            "revision_count": project.revision_count,
            "created_at": project.created_at, "updated_at": project.updated_at,
            "message_count": msg_count.scalar() or 0,
            "work_count": work_count.scalar() or 0,
            "reference_count": ref_count.scalar() or 0,
            "environment_count": env_count.scalar() or 0,
        }

    async def get_project_environments(self, db: AsyncSession, project_id: int) -> list:
        result = await db.execute(
            select(RLEnvironment).where(RLEnvironment.research_project_id == project_id)
            .order_by(RLEnvironment.created_at)
        )
        envs = result.scalars().all()
        return [
            {
                "id": e.id, "name": e.name, "slug": e.slug,
                "description": e.description, "domain": e.domain,
                "observation_space": e.observation_space,
                "action_space": e.action_space,
                "reward_description": e.reward_description,
                "difficulty": e.difficulty, "status": e.status,
                "test_results": json.loads(e.test_results_json) if e.test_results_json else None,
            }
            for e in envs
        ]

    async def get_project_training_runs(self, db: AsyncSession, project_id: int) -> list:
        env_ids_result = await db.execute(
            select(RLEnvironment.id).where(RLEnvironment.research_project_id == project_id)
        )
        env_ids = [r[0] for r in env_ids_result.fetchall()]
        if not env_ids:
            return []

        runs_result = await db.execute(
            select(TrainingRun).where(TrainingRun.env_id.in_(env_ids)).order_by(TrainingRun.created_at)
        )
        runs = runs_result.scalars().all()
        out = []
        for run in runs:
            er = await db.execute(select(RLEnvironment.name).where(RLEnvironment.id == run.env_id))
            env_name = er.scalar() or f"Env {run.env_id}"
            res = json.loads(run.results_json) if run.results_json else {}
            curve = json.loads(run.training_curve_json) if run.training_curve_json else []
            out.append({
                "id": run.id, "env_id": run.env_id, "env_name": env_name,
                "algorithm": run.algorithm, "status": run.status,
                "mean_reward": res.get("mean_reward"), "success_rate": res.get("success_rate"),
                "training_time_sec": res.get("training_time_sec"),
                "total_timesteps": res.get("total_timesteps"),
                "curve": curve,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            })
        return out

    async def get_chatboard(self, db: AsyncSession, project_id: int) -> List[AgentMessage]:
        result = await db.execute(
            select(AgentMessage).where(AgentMessage.project_id == project_id).order_by(AgentMessage.created_at)
        )
        return result.scalars().all()

    async def get_agent_work(self, db: AsyncSession, project_id: int, agent_name: str) -> List[AgentWork]:
        result = await db.execute(
            select(AgentWork).where(
                AgentWork.project_id == project_id,
                AgentWork.agent_name == agent_name,
            ).order_by(AgentWork.created_at)
        )
        return result.scalars().all()

    async def get_paper(self, db: AsyncSession, project_id: int) -> Optional[ResearchPaper]:
        result = await db.execute(
            select(ResearchPaper).where(ResearchPaper.project_id == project_id).order_by(ResearchPaper.created_at.desc())
        )
        return result.scalars().first()

    async def _paper_from_env_pipeline(self, db: AsyncSession, project_id: int, env_id: int,
                                       topic: Optional[str] = None,
                                       user_id: Optional[int] = None):
        """Run analyze → write → review on an existing env, populating the pre-created project."""
        result = await db.execute(select(ResearchProject).where(ResearchProject.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            logger.error(f"[Lab] paper_from_env: project {project_id} not found")
            return

        env_result = await db.execute(select(RLEnvironment).where(RLEnvironment.id == env_id))
        env = env_result.scalar_one_or_none()
        if not env:
            logger.error(f"[Lab] paper_from_env: env {env_id} not found")
            return

        env.research_project_id = project.id
        await db.commit()

        if topic:
            try:
                await self._search_and_import_topic_papers(db, project, min_papers=8)
            except Exception as e:
                logger.warning(f"[Lab] Paper references import failed: {e}")

        runs_result = await db.execute(
            select(TrainingRun).where(TrainingRun.env_id == env_id).order_by(TrainingRun.created_at)
        )
        runs = runs_result.scalars().all()

        results_data = []
        for run in runs:
            res = json.loads(run.results_json) if run.results_json else {}
            curve = json.loads(run.training_curve_json) if run.training_curve_json else []
            results_data.append({
                "run_id": run.id, "env_id": run.env_id, "env_name": env.name,
                "algorithm": run.algorithm, "status": run.status,
                "mean_reward": res.get("mean_reward"), "std_reward": res.get("std_reward"),
                "success_rate": res.get("success_rate"),
                "training_time_sec": res.get("training_time_sec"),
                "total_timesteps": res.get("total_timesteps"),
                "curve_length": len(curve),
            })

        env_summary = (
            f"**{env.name}** (domain: {env.domain}, difficulty: {env.difficulty})\n"
            f"- Observation Space: {env.observation_space}\n"
            f"- Action Space: {env.action_space}\n"
            f"- Reward: {env.reward_description}\n"
        )
        await self._save_message(db, project.id, "atlas", f"Using existing environment:\n{env_summary}", "design")
        await self._save_work(db, project.id, "atlas", "environments", "Generated Environments", env_summary,
                              metadata={"environments": [{"id": env.id, "name": env.name}]})

        completed = [r for r in results_data if r["status"] == "completed"]
        if completed:
            summary = f"## Training Results\n\n**{len(completed)} completed** out of {len(results_data)} runs.\n\n"
            for r in completed:
                summary += f"### {r['env_name']} — {r['algorithm']}\n"
                summary += f"- Mean Reward: **{r['mean_reward']}** (std: {r['std_reward']})\n"
                summary += f"- Success Rate: **{r['success_rate']}**\n"
                summary += f"- Training Time: {r['training_time_sec']}s | Timesteps: {r['total_timesteps']}\n\n"
            await self._save_message(db, project.id, "atlas", summary, "experiment")
            await self._save_work(db, project.id, "atlas", "training_results", "Training Results", summary,
                                  metadata={"runs": results_data})
        await db.commit()

        for phase_name in ["analyze", "write", "review"]:
            try:
                result = await db.execute(select(ResearchProject).where(ResearchProject.id == project_id))
                project = result.scalar_one_or_none()
                if not project or project.status == "completed":
                    break

                runner = {"analyze": self._run_analyze, "write": self._run_write, "review": self._run_review}[phase_name]
                await runner(db, project)

                if project.status != "completed" and phase_name in PHASES:
                    idx = PHASES.index(phase_name)
                    if idx + 1 < len(PHASES):
                        project.current_phase = PHASES[idx + 1]
                    else:
                        project.status = "completed"
                project.updated_at = datetime.utcnow()
                await db.commit()
            except Exception as e:
                logger.exception(f"[Lab] paper_from_env phase {phase_name} failed")
                try:
                    await self._save_message(db, project.id, "sage", f"Phase failed: {str(e)[:500]}", phase_name)
                    await db.commit()
                except Exception:
                    pass
                break

    async def delete_project(self, db: AsyncSession, project_id: int) -> bool:
        result = await db.execute(select(ResearchProject).where(ResearchProject.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            return False
        await db.delete(project)
        await db.commit()
        return True


lab_service = LabService()
