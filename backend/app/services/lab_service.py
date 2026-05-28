"""
Research Lab Service — Automated RL Research Pipeline

Phases: hypothesis → design → experiment → analyze → write → review

hypothesis: Formulate original hypothesis from user's idea (NO ArXiv)
design:     Generate Gymnasium environments from hypothesis specs
experiment: Train agents with configured algorithms
analyze:    Interpret real training results against hypothesis
write:      Search ArXiv for supporting literature + write full paper
review:     Peer review the draft

Agents: Sage (Research Strategist) + Atlas (RL Engineer)

The pipeline generates REAL RL environments and trains REAL agents,
producing papers backed by actual experimental data.
"""
import json
import logging
import re
import asyncio
import contextvars
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

_active_usage_acc = contextvars.ContextVar("_active_usage_acc", default=None)

from app.models import (
    ResearchProject, AgentMessage, AgentWork, ResearchPaper,
    Article, ProjectReference, RLEnvironment, EnvVersion, TrainingRun, User,
)
from app.database import async_session

logger = logging.getLogger("lab")

PHASES = ["hypothesis", "design", "experiment", "analyze", "write", "review"]

AGENTS = {
    "sage": {
        "name": "Sage",
        "role": "Research Strategist",
        "color": "#f59e0b",
        "model_preference": "kimi",
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

    async def _call_agent(self, agent_key: str, system_prompt: str, user_prompt: str, max_tokens: int = 16000, usage_acc=None) -> str:
        from app.services.ai_service import ai_service
        acc = usage_acc or _active_usage_acc.get(None)
        agent = AGENTS[agent_key]
        pref = agent["model_preference"]
        if pref == "kimi":
            try:
                return await ai_service._call_kimi(system_prompt, user_prompt, max_tokens=max_tokens, usage_acc=acc)
            except Exception:
                pass
        elif pref == "sonnet":
            try:
                return await ai_service._call_claude(system_prompt, user_prompt, model="claude-sonnet-4-6", max_tokens=max_tokens, usage_acc=acc)
            except Exception:
                pass
        try:
            return await ai_service._call_claude(system_prompt, user_prompt, model="claude-sonnet-4-6", max_tokens=max_tokens, usage_acc=acc)
        except Exception:
            pass
        return await ai_service._call_openai(system_prompt, user_prompt, max_tokens=min(max_tokens, 4096), usage_acc=acc)

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

    # ── Phase 1: Hypothesis ─────────────────────────────────────

    async def _run_hypothesis(self, db: AsyncSession, project: ResearchProject):
        logger.info(f"[Lab] HYPOTHESIS phase for project {project.id}")

        topic = project.topic or project.title
        description = project.description or ""

        prompt = (
            f"You are formulating an ORIGINAL research hypothesis for an RL study. "
            f"The user has provided this specific research idea:\n\n"
            f"{'=' * 60}\n"
            f"TOPIC: \"{topic}\"\n"
            f"{f'DESCRIPTION: {description}' if description else ''}\n"
            f"{'=' * 60}\n\n"
            f"IMPORTANT: You must treat the user's description as the CORE of the research. "
            f"Do NOT dilute, simplify, or generalize their idea. Every aspect of their description "
            f"must be directly reflected in the hypothesis and experimental design.\n\n"
            f"DO NOT reference any external papers or literature. This phase is about formulating "
            f"an ORIGINAL hypothesis purely from the user's idea. Literature will come later.\n\n"
            f"Create a research plan with:\n\n"
            f"1. **Research Question** — A specific, testable question that directly captures "
            f"the FULL scope of the user's idea. If they mention agent behavior, environment dynamics, "
            f"AND learning mechanisms, the question must address ALL of these.\n\n"
            f"2. **Hypothesis** — A clear, falsifiable hypothesis. Break it into sub-hypotheses if "
            f"the user's idea has multiple aspects (e.g., environment dynamics + agent self-observation "
            f"+ experience-based learning).\n\n"
            f"3. **Experimental Design** — Design RL environments that test EVERY aspect of the hypothesis. "
            f"This is critical: the environment design must include:\n"
            f"   - **Environment dynamics** — How the environment behaves and changes\n"
            f"   - **Agent observation requirements** — What the agent MUST observe, including "
            f"self-observation data (own action history, reward history, strategy effectiveness)\n"
            f"   - **Agent experience storage** — How the agent tracks and uses past experience\n"
            f"   - **Reward structure** — How rewards are shaped to encourage the target behavior\n"
            f"   - **Success criteria** — What constitutes the agent 'solving' the environment\n\n"
            f"4. **Expected Outcomes** — What results confirm or reject EACH sub-hypothesis?\n\n"
            f"CRITICAL: Include a structured JSON block at the end:\n\n"
            f"===RESEARCH_PLAN===\n"
            f'{{\n'
            f'  "hypothesis": "the full hypothesis, covering all aspects of the user\'s idea",\n'
            f'  "sub_hypotheses": ["H1: ...", "H2: ...", "H3: ..."],\n'
            f'  "environments": [\n'
            f'    {{\n'
            f'      "name": "descriptive name directly reflecting the research topic",\n'
            f'      "description": "EXTREMELY DETAILED description. This is the blueprint for building '
            f'a Gymnasium environment. You MUST specify:\\n'
            f'1. OBSERVATION SPACE: List every dimension. Include environment state AND agent self-observation '
            f'(own recent actions, recent rewards, strategy metrics, internal state estimates).\\n'
            f'2. ACTION SPACE: What actions the agent takes.\\n'
            f'3. TRANSITION DYNAMICS: How the environment changes, especially any dynamic/adaptive elements.\\n'
            f'4. REWARD FUNCTION: Exact reward structure. Include rewards for the TARGET behavior from the hypothesis '
            f'(e.g., reward for adapting, reward for using experience, penalty for repeating failed strategies).\\n'
            f'5. EPISODE TERMINATION: When episodes end.\\n'
            f'6. AGENT-SIDE REQUIREMENTS: Any self-observation, experience tracking, or meta-learning '
            f'mechanisms that must be built into the observation space or reward.",\n'
            f'      "domain": "one of: control, game, finance, robotics, navigation, optimization, custom",\n'
            f'      "difficulty": "easy or medium or hard",\n'
            f'      "variant_role": "treatment | baseline | control",\n'
            f'      "variant_label": "short human tag, e.g. with self-observation"\n'
            f'    }}\n'
            f'  ],\n'
            f'  "training_config": {{\n'
            f'    "algorithms": ["PPO", "SAC"],\n'
            f'    "timesteps": 50000,\n'
            f'    "n_seeds": 1\n'
            f'  }},\n'
            f'  "metrics": ["mean_reward", "success_rate", "convergence_speed"]\n'
            f'}}\n'
            f'===END_PLAN===\n\n'
        )

        exp_cfg = self._load_experiment_config(project)
        if exp_cfg and exp_cfg.get("env_variants"):
            variants = exp_cfg["env_variants"]
            algos = exp_cfg.get("algorithms") or ["PPO"]
            timesteps = exp_cfg.get("timesteps", 50000)
            n_seeds = exp_cfg.get("n_seeds", 1)
            variants_block = "\n".join(
                f"  {i+1}. [{v.get('role','treatment').upper()}] {v.get('label','variant')} — "
                f"{(v.get('modifier') or '(no extra modifier; the canonical version)').strip()}"
                for i, v in enumerate(variants)
            )
            prompt += (
                "USER-DEFINED ABLATION SETUP (MANDATORY — DO NOT DEVIATE):\n"
                f"You MUST design exactly {len(variants)} environments, one per variant below. "
                "Each environment must share the SAME base task, observation/action shape, episode "
                "length and reward scale; the ONLY difference between siblings is the `modifier`. "
                "This is critical: a baseline/treatment comparison is only valid when everything else "
                "is held constant.\n\n"
                f"{variants_block}\n\n"
                f"In the JSON plan, the `environments` array MUST contain {len(variants)} entries in "
                "the same order as the variants above. Each entry MUST include `variant_role` and "
                "`variant_label` matching the variant.\n\n"
                f"`training_config.algorithms` MUST equal {algos}, `training_config.timesteps` MUST "
                f"equal {timesteps}, `training_config.n_seeds` MUST equal {n_seeds}.\n\n"
                "Names should directly reflect the research topic AND the variant role."
            )
        else:
            prompt += (
                "Design exactly 2 environments that test different aspects of the hypothesis. "
                "Each env description must be detailed enough for an AI code generator to build a "
                "complete Gymnasium environment including ALL agent-side observation requirements. "
                "Names should directly reflect the research topic. "
                "For each environment, also set `variant_role` (`treatment` for the hypothesis-applied "
                "version, `baseline` for the control without it) and a short `variant_label`."
            )

        response = await self._call_agent("sage", AGENTS["sage"]["system_prompt"], prompt)
        await self._save_message(db, project.id, "sage", response, "hypothesis")

        plan = self._parse_research_plan(response)
        # Whenever a user-supplied config exists, force its values into the plan
        # so downstream phases use the user's choices regardless of LLM compliance.
        if plan and exp_cfg:
            plan.setdefault("training_config", {})
            plan["training_config"]["algorithms"] = exp_cfg.get("algorithms") or plan["training_config"].get("algorithms", ["PPO"])
            plan["training_config"]["timesteps"] = exp_cfg.get("timesteps", plan["training_config"].get("timesteps", 50000))
            plan["training_config"]["n_seeds"] = exp_cfg.get("n_seeds", 1)
            plan["training_config"]["n_eval_episodes"] = exp_cfg.get("n_eval_episodes", 10)
            if exp_cfg.get("hyperparams"):
                plan["training_config"]["hyperparams"] = exp_cfg["hyperparams"]
            # Ensure each env spec carries its variant role/label even if the LLM forgot.
            user_variants = exp_cfg.get("env_variants") or []
            llm_envs = plan.get("environments") or []
            if len(llm_envs) < len(user_variants):
                # Pad with stubs the design phase will still attempt to render.
                for v in user_variants[len(llm_envs):]:
                    llm_envs.append({
                        "name": v.get("label", "variant"),
                        "description": v.get("modifier", "") or v.get("label", ""),
                        "domain": "custom", "difficulty": "medium",
                    })
                plan["environments"] = llm_envs
            for env_spec, var in zip(plan.get("environments", []), user_variants):
                env_spec["variant_role"] = var.get("role", "treatment")
                env_spec["variant_label"] = var.get("label", "")
                if var.get("modifier") and "modifier" not in env_spec:
                    env_spec["modifier"] = var["modifier"]

        if plan:
            project.selected_idea = json.dumps(plan)
            await self._save_work(db, project.id, "sage", "hypothesis", "Research Hypothesis", response, metadata=plan)
        else:
            project.selected_idea = response
            await self._save_work(db, project.id, "sage", "hypothesis", "Research Hypothesis", response)

        await db.commit()

    # ── Phase 2: Design ──────────────────────────────────────────

    async def _run_design(self, db: AsyncSession, project: ResearchProject):
        logger.info(f"[Lab] DESIGN phase for project {project.id}")
        from app.services.architect_service import architect_service
        from app.services.sandbox_runner import sandbox_runner

        plan = self._parse_research_plan(project.selected_idea or "")
        env_specs = plan.get("environments", [])

        if not env_specs:
            history = await self._get_conversation_history(db, project.id, ["hypothesis", "research"])
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

        topic = project.topic or project.title
        description = project.description or ""
        hypothesis_text = plan.get("hypothesis", "")
        sub_hypotheses = plan.get("sub_hypotheses", [])
        hypothesis_prefix = ""
        if hypothesis_text or description:
            parts = [f"RESEARCH HYPOTHESIS: {hypothesis_text}"] if hypothesis_text else []
            if sub_hypotheses:
                parts.append("SUB-HYPOTHESES: " + "; ".join(sub_hypotheses))
            if description:
                parts.append(f"USER'S ORIGINAL IDEA: {description}")
            hypothesis_prefix = "\n".join(parts) + "\n\nENVIRONMENT SPECIFICATION:\n"

        # If the user supplied an experiment_config, we drop the hard cap so all
        # requested variants get generated; otherwise keep the legacy 3-env safety cap.
        exp_cfg = self._load_experiment_config(project)
        max_envs = max(len(exp_cfg.get("env_variants", [])), 1) if exp_cfg else 3
        env_specs_to_build = env_specs[:max_envs]

        generated_envs = []
        for i, spec in enumerate(env_specs_to_build):
            env_name = spec.get("name", f"Research Env {i+1}")
            env_desc = spec.get("description", env_name)
            env_domain = spec.get("domain", "custom")
            env_difficulty = spec.get("difficulty", "medium")
            variant_role = (spec.get("variant_role") or "").strip().lower() or None
            variant_label = (spec.get("variant_label") or "").strip() or None
            variant_modifier = (spec.get("modifier") or "").strip()

            full_desc_parts = [hypothesis_prefix + env_desc]
            if variant_label or variant_role or variant_modifier:
                tag_line = (
                    f"\n\nABLATION VARIANT: {variant_role or 'treatment'} — "
                    f"{variant_label or 'variant'}"
                )
                if variant_modifier:
                    tag_line += (
                        "\nMODIFIER (apply ONLY this difference vs. sibling variants; everything else "
                        f"must be IDENTICAL across variants): {variant_modifier}"
                    )
                full_desc_parts.append(tag_line)
            full_desc = "".join(full_desc_parts)

            await self._save_message(
                db, project.id, "atlas",
                f"**Environment {i+1}/{len(env_specs_to_build)}:** Generating *{env_name}*"
                + (f" _(variant: {variant_label or variant_role})_" if (variant_label or variant_role) else "")
                + "...",
                "design"
            )
            await db.commit()

            try:
                gen = await architect_service.generate_env_code(full_desc, env_domain, env_difficulty)
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

                final_name = env_name if env_name and env_name != "custom-env" else gen.get("name", env_name)
                if final_name in ("custom-env", "CustomEnv", "custom_env") or not final_name:
                    final_name = f"{project.topic or project.title} - Env {i+1}"

                slug_base = self._slugify(final_name)
                existing_slug = await db.execute(select(RLEnvironment).where(RLEnvironment.slug == slug_base))
                if existing_slug.scalar_one_or_none():
                    slug_base = f"{slug_base}-{int(datetime.utcnow().timestamp())}"

                env = RLEnvironment(
                    name=final_name,
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
                    variant_role=variant_role,
                    variant_label=variant_label,
                )
                db.add(env)
                await db.flush()

                v1 = EnvVersion(env_id=env.id, version=1, code=code, spec_json=spec_json,
                                change_summary="Generated by Research Lab")
                db.add(v1)
                await db.flush()

                generated_envs.append({
                    "id": env.id, "name": env.name,
                    "variant_role": variant_role,
                    "variant_label": variant_label,
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

        summary = f"**Design complete.** {len(generated_envs)}/{len(env_specs_to_build)} environments built.\n"
        for e in generated_envs:
            tag = ""
            if e.get("variant_label") or e.get("variant_role"):
                tag = f" _[{e.get('variant_role') or 'variant'}: {e.get('variant_label') or '—'}]_"
            summary += f"- **{e['name']}**{tag} (ID: {e['id']}) — {e['tests_passed']}/{e['tests_total']} tests\n"

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
        all_environments = result.scalars().all()

        environments = []
        skipped = []
        for env in all_environments:
            if env.test_results_json:
                try:
                    tr = json.loads(env.test_results_json)
                    if tr.get("passed", 0) < tr.get("total", 8) * 0.75:
                        skipped.append(env.name)
                        continue
                except (json.JSONDecodeError, TypeError):
                    pass
            environments.append(env)

        if skipped:
            await self._save_message(
                db, project.id, "atlas",
                f"Skipping {len(skipped)} environment(s) with insufficient test coverage: {', '.join(skipped)}",
                "experiment"
            )

        if not environments:
            await self._save_message(db, project.id, "atlas", "No valid environments available. Skipping training.", "experiment")
            await db.commit()
            return

        plan = self._parse_research_plan(project.selected_idea or "")
        tc = plan.get("training_config", {}) if plan else {}
        exp_cfg = self._load_experiment_config(project)

        # Source of truth for algos/timesteps/seeds: user's experiment_config when present,
        # otherwise the LLM-generated training_config from the hypothesis phase.
        supported = {"PPO", "SAC", "DQN", "A2C", "TD3", "QRDQN"}
        if exp_cfg:
            user_algos = [a.upper() for a in (exp_cfg.get("algorithms") or []) if a.upper() in supported]
            timesteps = int(exp_cfg.get("timesteps", 50000))
            n_seeds = max(1, int(exp_cfg.get("n_seeds", 1)))
            n_eval_episodes = int(exp_cfg.get("n_eval_episodes", 10))
            hyperparams = exp_cfg.get("hyperparams") or {}
        else:
            user_algos = [a.upper() for a in tc.get("algorithms", []) if a.upper() in supported]
            timesteps = int(tc.get("timesteps", 50000))
            n_seeds = 1
            n_eval_episodes = 10
            hyperparams = {}

        run_ids = []
        for env in environments:
            auto_algo = training_service._select_algorithm(env.code or "")
            if exp_cfg and user_algos:
                # User explicitly chose algorithms — honour them exactly, no auto/backup.
                algos = list(user_algos)
            else:
                algos = [auto_algo]
                for a in user_algos:
                    if a != auto_algo and a not in algos:
                        algos.append(a)
                        break
                if len(algos) < 2:
                    backup = "DQN" if auto_algo not in ("DQN",) else "PPO"
                    if backup not in algos:
                        algos.append(backup)

            for algo in algos:
                for seed_idx in range(n_seeds):
                    seed_value = seed_idx
                    config: dict = {
                        "total_timesteps": timesteps,
                        "algorithm": algo,
                        "n_eval_episodes": n_eval_episodes,
                        "seed": seed_value,
                        "variant_role": getattr(env, "variant_role", None),
                    }
                    if hyperparams.get("learning_rate") is not None:
                        config["learning_rate"] = hyperparams["learning_rate"]
                    if hyperparams.get("batch_size") is not None:
                        config["batch_size"] = hyperparams["batch_size"]
                    if hyperparams.get("gamma") is not None:
                        config["gamma"] = hyperparams["gamma"]
                    if hyperparams.get("net_arch"):
                        config["net_arch"] = hyperparams["net_arch"]
                    try:
                        run = await training_service.start_training(env.id, config, db)
                        run_ids.append(run.id)
                        seed_tag = f" seed={seed_value}" if n_seeds > 1 else ""
                        variant_tag = f" [{env.variant_role}]" if getattr(env, "variant_role", None) else ""
                        await self._save_message(
                            db, project.id, "atlas",
                            f"Training **{algo}** on **{env.name}**{variant_tag}{seed_tag} "
                            f"({timesteps:,} timesteps)...",
                            "experiment"
                        )
                    except Exception as e:
                        await self._save_message(
                            db, project.id, "atlas",
                            f"Failed to start {algo} on {env.name} (seed {seed_value}): {str(e)[:200]}",
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

        research_history = await self._get_conversation_history(db, project.id, ["hypothesis", "research"])

        # Build an ablation-aware results table for the analyst.
        ablation_table = await self._build_results_table(db, project.id)
        env_meta_res = await db.execute(
            select(RLEnvironment.variant_role).where(RLEnvironment.research_project_id == project.id)
        )
        roles_present = {r[0] for r in env_meta_res.fetchall() if r[0]}
        has_ablation = len(roles_present) >= 2

        ablation_instruction = (
            "\n\n**ABLATION COMPARISON (REQUIRED):** This study has variant roles "
            f"{sorted(roles_present)}. You MUST explicitly compare the *baseline* vs "
            "*treatment* (and control if present) per algorithm: report the absolute and "
            "relative difference in mean reward, success rate, and convergence speed, then "
            "state whether the hypothesis-applied variant outperforms its baseline and by "
            "how much. Quote concrete numbers from the table."
            if has_ablation else ""
        )

        prompt = (
            f"You are analyzing REAL experimental results from actual RL training runs.\n\n"
            f"**Original Hypothesis:**\n{research_history[:3000]}\n\n"
            f"**Training Results:**\n{results_text}\n\n"
            f"**Aggregated Results Table (mean±std across seeds, grouped by variant):**\n"
            f"{ablation_table or '(no aggregated table available)'}\n\n"
            f"**Training Curve Progression:**\n{curve_ctx}\n\n"
            f"Provide a thorough analysis:\n"
            f"1. **Key Findings** — What do the results show?\n"
            f"2. **Algorithm Comparison** — How do algorithms compare on each environment?\n"
            f"3. **Hypothesis Evaluation** — Was the hypothesis supported, refuted, or inconclusive?\n"
            f"4. **Convergence Analysis** — How quickly did each algorithm learn? Learning dynamics?\n"
            f"5. **Strengths & Limitations** — What worked and what didn't?\n"
            f"6. **Conclusions** — Key takeaways for the research community"
            f"{ablation_instruction}\n\n"
            f"Be rigorous and specific. These are real results from actual training, not simulations."
        )

        analysis = await self._call_agent("sage", AGENTS["sage"]["system_prompt"], prompt)
        await self._save_message(db, project.id, "sage", analysis, "analyze")
        await self._save_work(db, project.id, "sage", "analysis", "Results Analysis", analysis)
        await db.commit()

    # ── Phase 5: Write ───────────────────────────────────────────

    async def _build_results_table(self, db: AsyncSession, project_id: int) -> str:
        """Build a formatted results table from real training data.

        When multiple seeds exist for the same (env, algo) cell the rows are
        collapsed into mean±std across seeds, which is the standard way to
        report ablation results in an RL paper.
        """
        env_rows = await db.execute(
            select(RLEnvironment.id, RLEnvironment.name, RLEnvironment.variant_role, RLEnvironment.variant_label)
            .where(RLEnvironment.research_project_id == project_id)
        )
        env_meta = {
            r[0]: {"name": r[1], "variant_role": r[2], "variant_label": r[3]}
            for r in env_rows.fetchall()
        }
        if not env_meta:
            return ""

        runs_result = await db.execute(
            select(TrainingRun).where(
                TrainingRun.env_id.in_(list(env_meta.keys())),
                TrainingRun.status == "completed",
            ).order_by(TrainingRun.created_at)
        )
        runs = runs_result.scalars().all()
        if not runs:
            return ""

        # Group runs by (env_id, algorithm) and aggregate across seeds.
        from collections import defaultdict
        import math
        cells: dict = defaultdict(list)
        for run in runs:
            res = json.loads(run.results_json) if run.results_json else {}
            cells[(run.env_id, run.algorithm)].append(res)

        def _mean(xs):
            xs = [x for x in xs if isinstance(x, (int, float))]
            return sum(xs) / len(xs) if xs else None

        def _std(xs):
            xs = [x for x in xs if isinstance(x, (int, float))]
            if len(xs) < 2:
                return None
            m = sum(xs) / len(xs)
            return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))

        def _fmt(val, digits=3):
            if val is None:
                return "N/A"
            return f"{val:.{digits}f}"

        lines = [
            "| Variant | Environment | Algorithm | Seeds | Mean Reward ± Std | Success Rate | Train Time (s) |",
            "|---|---|---|---|---|---|---|",
        ]
        # Sort: baseline first, then treatment, then control, then misc; group by env.
        role_order = {"baseline": 0, "control": 1, "treatment": 2}

        def _sort_key(item):
            (env_id, algo), _ = item
            meta = env_meta.get(env_id, {})
            role = (meta.get("variant_role") or "zzz").lower()
            return (role_order.get(role, 99), meta.get("name", ""), algo)

        for (env_id, algo), results in sorted(cells.items(), key=_sort_key):
            meta = env_meta.get(env_id, {})
            env_name = meta.get("name") or f"Env {env_id}"
            role = meta.get("variant_role") or "—"
            label = meta.get("variant_label") or "—"
            variant_cell = f"{role}" + (f" ({label})" if label and label != "—" else "")

            mrs = [r.get("mean_reward") for r in results]
            srs = [r.get("success_rate") for r in results]
            times = [r.get("training_time_sec") for r in results]

            mean_r = _mean(mrs)
            std_r = _std(mrs) if len(mrs) > 1 else _mean([r.get("std_reward") for r in results])
            reward_cell = (
                f"{_fmt(mean_r)} ± {_fmt(std_r)}" if mean_r is not None else "N/A"
            )
            success_cell = (
                f"{_mean(srs) * 100:.1f}%" if _mean(srs) is not None else "N/A"
            )
            time_cell = _fmt(_mean(times), 1) if _mean(times) is not None else "N/A"
            lines.append(
                f"| {variant_cell} | {env_name} | {algo} | {len(results)} | "
                f"{reward_cell} | {success_cell} | {time_cell} |"
            )

        return "\n".join(lines)

    async def _build_curve_descriptions(self, db: AsyncSession, project_id: int) -> str:
        """Build textual descriptions of training curves for the paper."""
        env_ids_result = await db.execute(
            select(RLEnvironment.id, RLEnvironment.name).where(RLEnvironment.research_project_id == project_id)
        )
        env_map = {r[0]: r[1] for r in env_ids_result.fetchall()}
        if not env_map:
            return ""

        runs_result = await db.execute(
            select(TrainingRun).where(
                TrainingRun.env_id.in_(list(env_map.keys())), TrainingRun.status == "completed"
            ).order_by(TrainingRun.created_at)
        )
        runs = runs_result.scalars().all()
        descs = []
        for run in runs:
            if not run.training_curve_json:
                continue
            curve = json.loads(run.training_curve_json)
            if len(curve) < 2:
                continue
            rewards = [p.get("mean_reward", 0) for p in curve]
            env_name = env_map.get(run.env_id, f"Env {run.env_id}")
            q1 = rewards[:len(rewards)//4]
            q4 = rewards[3*len(rewards)//4:]
            early_avg = sum(q1)/max(len(q1), 1)
            late_avg = sum(q4)/max(len(q4), 1)
            peak = max(rewards)
            improvement = late_avg - early_avg
            descs.append(
                f"**{env_name} + {run.algorithm}:** "
                f"Initial reward ~{early_avg:.2f}, final reward ~{late_avg:.2f} "
                f"(improvement: {improvement:+.2f}), peak: {peak:.2f}, "
                f"{len(curve)} evaluation points over training."
            )
        return "\n".join(descs) if descs else "No curve data available."

    async def _run_write(self, db: AsyncSession, project: ResearchProject):
        logger.info(f"[Lab] WRITE phase — literature search + paper drafting for project {project.id}")

        # ── Step 1: Search ArXiv for supporting references ────────
        await self._save_message(
            db, project.id, "sage",
            "Searching ArXiv for related literature to support our findings...",
            "write",
        )
        try:
            ref_count_res = await db.execute(
                select(func.count(ProjectReference.id)).where(ProjectReference.project_id == project.id)
            )
            current_refs = ref_count_res.scalar() or 0
            if current_refs < 10:
                logger.info(f"[Lab] Write phase: {current_refs} refs, searching ArXiv...")
                await self._search_and_import_topic_papers(db, project, min_papers=max(10, 15 - current_refs))
                new_count_res = await db.execute(
                    select(func.count(ProjectReference.id)).where(ProjectReference.project_id == project.id)
                )
                logger.info(f"[Lab] Write phase: now {new_count_res.scalar() or 0} refs after search")
        except Exception as e:
            logger.warning(f"[Lab] ArXiv search failed in write phase: {e}")

        # ── Step 2: Gather all context ────────────────────────────
        works_result = await db.execute(
            select(AgentWork).where(AgentWork.project_id == project.id).order_by(AgentWork.created_at)
        )
        all_works = works_result.scalars().all()
        works_text = "\n\n---\n\n".join([
            f"[{w.work_type}] {w.title}\n{w.content[:4000]}" for w in all_works
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

        results_table = await self._build_results_table(db, project.id)
        curve_desc = await self._build_curve_descriptions(db, project.id)

        refs_result = await db.execute(
            select(Article).join(ProjectReference, ProjectReference.article_id == Article.id).where(
                ProjectReference.project_id == project.id
            ).order_by(Article.relevance_score.desc().nullslast()).limit(15)
        )
        ref_articles = refs_result.scalars().all()
        refs_for_bib = []
        for i, art in enumerate(ref_articles, 1):
            arxiv_tag = f" arXiv:{art.arxiv_id}" if art.arxiv_id else ""
            refs_for_bib.append(f"[{i}] {art.title}.{arxiv_tag}")
        bib_text = "\n".join(refs_for_bib) if refs_for_bib else "No references available."
        ref_summaries = []
        for i, art in enumerate(ref_articles[:8], 1):
            summary = art.summary or (art.content[:400] + "..." if art.content and len(art.content) > 400 else art.content or "")
            ref_summaries.append(f"[{i}] {art.title}: {summary}")
        ref_ctx = "\n\n".join(ref_summaries)

        topic = project.topic or project.title
        description = project.description or ""

        hypothesis_work = None
        for w in all_works:
            if w.work_type == "hypothesis":
                hypothesis_work = w
                break

        hypothesis_ctx = ""
        if hypothesis_work:
            hypothesis_ctx = hypothesis_work.content[:5000]
        elif project.selected_idea:
            hypothesis_ctx = project.selected_idea[:5000]

        # ── Step 3: Write paper with hypothesis as central thread ─
        prompt = (
            f"Write a COMPLETE research paper formatted for submission to the "
            f"**Reinforcement Learning Conference (RLC 2026 / RLJ 2026)**, following the official RLC/RLJ "
            f"submission format described below.\n\n"
            f"{'=' * 60}\n"
            f"CORE RESEARCH IDEA (this is the CENTRAL THREAD of the entire paper):\n"
            f"Topic: \"{topic}\"\n"
            f"{f'Description: {description}' if description else ''}\n"
            f"{'=' * 60}\n\n"
            f"**Our Original Hypothesis:**\n{hypothesis_ctx}\n\n"
            f"This paper is based on REAL experiments. We built actual RL environments and trained real agents.\n\n"
            f"**Environment Specifications:**\n{env_ctx}\n\n"
            f"**Experimental Results Table:**\n{results_table}\n\n"
            f"**Training Curve Analysis:**\n{curve_desc}\n\n"
            f"**Related Literature (use as SUPPORTING references, not as the basis of the paper):**\n{ref_ctx}\n\n"
            f"**Bibliography entries:**\n{bib_text}\n\n"
            f"CRITICAL FRAMING INSTRUCTION:\n"
            f"The paper's narrative must flow from OUR ORIGINAL HYPOTHESIS, not from the literature. "
            f"The structure is: We had this idea → we designed experiments to test it → here are our results → "
            f"literature supports/contrasts our findings. The ArXiv references are SUPPORTING citations, "
            f"NOT the foundation of the paper. Our contribution is ORIGINAL.\n\n"
            f"{'=' * 60}\n"
            f"RLC 2026 FORMAT & LENGTH RULES (MUST FOLLOW EXACTLY):\n"
            f"- The MAIN TEXT must be **6–8 content pages** (≈ 4,000–5,500 words). References and appendices "
            f"do NOT count toward this limit. Do NOT pad; be concise and precise like a real RLC paper.\n"
            f"- A COVER PAGE precedes the paper: it contains a Summary and a Contributions list (see below).\n"
            f"- Appendices are PERMITTED, come AFTER the references, and are NOT counted toward the page limit. "
            f"Place supporting detail (extra tables, derivations, hyperparameter grids, additional plots) there.\n"
            f"- Use author–year citation style consistent with natbib (e.g., '(Sutton & Barto, 1998)' for "
            f"parenthetical, 'Sutton & Barto (1998)' when the authors are part of the sentence). "
            f"Cite at least 5 of the provided references.\n"
            f"- Figures: caption goes AFTER the figure, lowercase except first word/proper nouns, numbered consecutively. "
            f"Tables: caption goes BEFORE the table. Always reference figures/tables in the text before they appear.\n\n"
            f"{'=' * 60}\n"
            f"PAPER STRUCTURE (output in this exact order, using markdown headings):\n\n"
            f"# [Paper Title — directly reflecting our hypothesis about \"{topic}\"]\n\n"
            f"## Summary\n"
            f"COVER PAGE element. One or two short paragraphs (may differ from the abstract) describing the work "
            f"for the cover page. This is NOT counted toward the page limit.\n\n"
            f"## Contributions\n"
            f"COVER PAGE element. A succinct, precise NUMBERED list of the paper's contributions. "
            f"For each contribution, add a 'Context:' note on the next line situating it relative to prior work "
            f"(write 'Context: None' if there is no additional context). Keep each contribution to roughly one "
            f"sentence. Submissions are judged mostly on these claims, so scope them carefully and do NOT overclaim. "
            f"Every major contribution claimed here must also appear in the main text.\n\n"
            f"## Abstract\n"
            f"A SINGLE paragraph (150–250 words). State OUR hypothesis, OUR approach, and OUR key results with numbers.\n\n"
            f"## 1 Introduction\n"
            f"Start with the problem WE identified. State OUR motivation and OUR hypothesis. "
            f"Briefly list OUR contributions. Reference related work only to establish context. ~500 words.\n\n"
            f"## 2 Related Work\n"
            f"Position OUR work relative to existing literature using author–year citations. "
            f"Emphasize what existing work does NOT address that WE do. ~350 words.\n\n"
            f"## 3 Methodology\n"
            f"### 3.1 Environment Design\n"
            f"Describe each environment — state space, action space, transition dynamics, reward function. "
            f"Explain how each design choice directly tests our hypothesis.\n"
            f"### 3.2 Agent Architecture\n"
            f"If the hypothesis involves agent-side mechanisms (self-observation, experience storage, etc.), "
            f"describe how they are implemented in the observation space and reward structure.\n"
            f"### 3.3 Algorithm Selection\n"
            f"Justify algorithm choices in context of the hypothesis.\n\n"
            f"## 4 Experimental Setup\n"
            f"Training configuration, evaluation protocol, metrics. Move long hyperparameter grids to the appendix.\n\n"
            f"## 5 Results\n"
            f"### 5.1 Quantitative Results\n{results_table}\n\n"
            f"Discuss each result IN RELATION TO THE HYPOTHESIS. Which sub-hypotheses are supported?\n"
            f"### 5.2 Learning Dynamics\n{curve_desc}\n"
            f"What do the curves tell us about our hypothesis?\n\n"
            f"## 6 Discussion\n"
            f"Key findings relative to hypothesis. Implications. Comparison with prior work. "
            f"Limitations and threats to validity.\n\n"
            f"## 7 Conclusion\n"
            f"Which hypotheses confirmed/rejected? Main takeaways. Future work.\n\n"
            f"## Broader Impact Statement\n"
            f"OPTIONAL short section discussing potential repercussions / negative impacts a user of this research "
            f"should be aware of. Keep it to a short paragraph; omit only if genuinely not applicable.\n\n"
            f"## References\n"
            f"List the cited references in alphabetical order by first author. These do NOT count toward the page limit.\n\n"
            f"## Appendix\n"
            f"### A Implementation & Hyperparameter Details\n"
            f"Full training configuration, hyperparameter tables, and reproducibility details.\n"
            f"### B Additional Results\n"
            f"Extra plots, per-environment breakdowns, or derivations that support but are not central to the main claims. "
            f"Appendices are NOT counted toward the 6–8 page limit.\n\n"
            f"{'=' * 60}\n"
            f"CRITICAL INSTRUCTIONS:\n"
            f"- The ENTIRE paper revolves around OUR hypothesis about \"{topic}\"; every section connects back to it.\n"
            f"- Keep the MAIN TEXT (Introduction through Conclusion) within 6–8 pages worth of content. "
            f"Push detail to the appendix rather than bloating the main text.\n"
            f"- Use EXACT numbers from the experimental results.\n"
            f"- Use author–year citations and cite at least 5 references.\n"
            f"- Write the COMPLETE paper, do NOT truncate any section.\n"
            f"- Formal academic English throughout.\n"
            f"- Use markdown # for the title, ## for sections (Summary, Contributions, Abstract, numbered sections, "
            f"Broader Impact Statement, References, Appendix), and ### for subsections."
        )

        paper_content = await self._call_agent("sage", AGENTS["sage"]["system_prompt"], prompt)

        if len(paper_content) < 2000:
            continuation_prompt = (
                f"The paper draft is incomplete. Continue writing from where you left off. "
                f"Here is the current content:\n\n{paper_content}\n\n"
                f"Continue the paper from the last section. Write all remaining sections in full."
            )
            continuation = await self._call_agent("sage", AGENTS["sage"]["system_prompt"], continuation_prompt)
            paper_content = paper_content + "\n\n" + continuation

        await self._save_message(db, project.id, "sage", "Paper draft complete.", "write")

        lines = paper_content.split("\n")
        title = project.title
        for line in lines[:10]:
            clean = line.replace("#", "").strip()
            low = clean.lower()
            if clean and len(clean) > 10 and low not in ("summary", "contributions", "abstract") \
                    and not low.startswith(("summary", "contributions", "abstract")):
                title = clean
                break

        # Extract the Abstract paragraph specifically from the "## Abstract" heading,
        # so that the cover-page Summary/Contributions (which precede it) are not mistaken for it.
        abstract = ""
        abs_started = False
        abs_lines = []
        for line in lines:
            stripped = line.strip()
            heading = stripped.lstrip("#").strip().lower()
            if not abs_started:
                if stripped.startswith("#") and heading == "abstract":
                    abs_started = True
                continue
            if stripped.startswith("#"):
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

        # Email notification: paper ready
        try:
            from app.services.email_service import email_service
            if project.user_id:
                user_obj = (await db.execute(
                    select(User).where(User.id == project.user_id)
                )).scalar_one_or_none()
                if user_obj and user_obj.email and user_obj.email_notifications:
                    await email_service.send_transactional(
                        to=user_obj.email, template="paper_ready",
                        data={"title": title, "project_id": project.id},
                        user_id=user_obj.id,
                    )
        except Exception:
            pass

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
                             topic: Optional[str] = None, user_id: Optional[int] = None,
                             experiment_config_json: Optional[str] = None) -> ResearchProject:
        project = ResearchProject(
            title=title, description=description, topic=topic, user_id=user_id,
            experiment_config_json=experiment_config_json,
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        logger.info(
            "[Lab] Created project: %s (id=%d, advanced_settings=%s)",
            title, project.id, bool(experiment_config_json),
        )
        return project

    def _load_experiment_config(self, project: ResearchProject) -> Optional[dict]:
        """Return the validated experiment_config dict for a project, or None."""
        raw = getattr(project, "experiment_config_json", None)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning("[Lab] project %d has malformed experiment_config_json", project.id)
            return None

    async def run_next_phase(self, db: AsyncSession, project_id: int) -> dict:
        result = await db.execute(select(ResearchProject).where(ResearchProject.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            return {"error": "Project not found"}
        if project.status == "completed":
            return {"error": "Project already completed"}
        if getattr(project, "phase_running", False):
            return {"error": "A phase is already running"}

        phase = project.current_phase
        logger.info(f"[Lab] Running phase: {phase} for project {project.id}")

        runners = {
            "hypothesis": self._run_hypothesis,
            "design": self._run_design,
            "experiment": self._run_experiment,
            "analyze": self._run_analyze,
            "write": self._run_write,
            "review": self._run_review,
            "research": self._run_hypothesis,
        }

        runner = runners.get(phase)
        if not runner:
            return {"error": f"Unknown phase: {phase}"}

        try:
            project.phase_running = True
            await db.commit()
        except Exception:
            pass

        try:
            await runner(db, project)
        except Exception as e:
            logger.exception(f"[Lab] Phase {phase} failed for project {project.id}")
            try:
                project.phase_running = False
                await self._save_message(db, project.id, "sage", f"Phase failed: {str(e)[:500]}", phase)
                await db.commit()
            except Exception:
                pass
            return {"error": str(e), "phase": phase}

        effective_phase = "hypothesis" if phase == "research" else phase
        if project.status != "completed" and effective_phase in PHASES:
            idx = PHASES.index(effective_phase)
            if idx + 1 < len(PHASES):
                project.current_phase = PHASES[idx + 1]
            else:
                project.status = "completed"

        project.phase_running = False
        project.updated_at = datetime.utcnow()
        await db.commit()

        # Email notification: research complete
        if project.status == "completed" and project.user_id:
            try:
                from app.services.email_service import email_service
                user_obj = (await db.execute(
                    select(User).where(User.id == project.user_id)
                )).scalar_one_or_none()
                if user_obj and user_obj.email and user_obj.email_notifications:
                    await email_service.send_transactional(
                        to=user_obj.email, template="research_complete",
                        data={"title": project.title, "project_id": project.id},
                        user_id=user_obj.id,
                    )
            except Exception:
                pass

        return {
            "phase_completed": phase,
            "next_phase": project.current_phase,
            "status": project.status,
        }

    async def replay_phase(self, db: AsyncSession, project_id: int, phase: str) -> dict:
        """Re-run a specific completed phase without advancing the project."""
        if phase not in PHASES:
            return {"error": f"Unknown phase: {phase}"}

        result = await db.execute(select(ResearchProject).where(ResearchProject.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            return {"error": "Project not found"}
        if getattr(project, "phase_running", False):
            return {"error": "A phase is already running"}

        effective_replay = "hypothesis" if phase == "research" else phase
        effective_current = "hypothesis" if project.current_phase == "research" else project.current_phase
        current_idx = PHASES.index(effective_current) if effective_current in PHASES else len(PHASES)
        replay_idx = PHASES.index(effective_replay) if effective_replay in PHASES else 0
        is_completed = project.status == "completed"

        if not is_completed and replay_idx >= current_idx:
            return {"error": f"Phase '{phase}' has not been completed yet"}

        runners = {
            "hypothesis": self._run_hypothesis,
            "design": self._run_design,
            "experiment": self._run_experiment,
            "analyze": self._run_analyze,
            "write": self._run_write,
            "review": self._run_review,
            "research": self._run_hypothesis,
        }
        runner = runners.get(phase)
        if not runner:
            return {"error": f"No runner for phase: {phase}"}

        logger.info(f"[Lab] REPLAY phase '{phase}' for project {project.id}")

        try:
            project.phase_running = True
            await db.commit()
        except Exception:
            pass

        saved_phase = project.current_phase
        saved_status = project.status

        try:
            await runner(db, project)
        except Exception as e:
            logger.exception(f"[Lab] Replay of phase '{phase}' failed for project {project.id}")
            try:
                project.phase_running = False
                await self._save_message(db, project.id, "sage", f"Replay of {phase} failed: {str(e)[:500]}", phase)
                await db.commit()
            except Exception:
                pass
            return {"error": str(e), "phase": phase}

        project.current_phase = saved_phase
        project.status = saved_status
        project.phase_running = False
        project.updated_at = datetime.utcnow()
        await db.commit()

        return {"phase_replayed": phase, "current_phase": project.current_phase, "status": project.status}

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
            "phase_running": getattr(project, "phase_running", False) or False,
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
