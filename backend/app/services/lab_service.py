import json
import logging
import subprocess
import sys
import tempfile
import os
import base64
from datetime import datetime
from typing import List, Optional, Dict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Article, ResearchProject, AgentMessage, AgentWork, ResearchPaper, ProjectReference

logger = logging.getLogger("lab")

PHASES = ["brainstorm", "discussion", "decision", "methodology", "experiments", "writing", "review"]

AGENTS = {
    "aria": {
        "name": "Prof. Aria",
        "role": "Principal Investigator & Literature Lead",
        "color": "#f59e0b",
        "model_preference": "kimi",
        "system_prompt": (
            "You are Professor Aria, Principal Investigator at a leading AI and Reinforcement Learning research lab. "
            "You have 20+ years of experience across machine learning, deep learning, NLP, computer vision, and RL. "
            "You combine the roles of PI and Literature Agent: you survey ArXiv for relevant work, identify RL environments, "
            "algorithms, and metrics from papers, and guide the team's research direction. "
            "You are visionary yet pragmatic; you identify high-impact research gaps, evaluate novelty rigorously, "
            "and guide your team toward publishable results. You ask penetrating questions, challenge weak assumptions, "
            "and synthesize ideas across subfields. You have final say on research direction but value your team's input. "
            "When evaluating ideas, consider: novelty, feasibility, potential impact, and whether the team can execute it "
            "with available resources. For RL projects specifically, you evaluate environment design, reward shaping, "
            "algorithm selection, and benchmark choices. Speak concisely and professionally. Never use emojis."
        ),
    },
    "marcus": {
        "name": "Dr. Marcus",
        "role": "ML Engineer / Experimentalist / Replication Specialist",
        "color": "#3b82f6",
        "model_preference": "kimi",
        "system_prompt": (
            "You are Dr. Marcus, a senior ML Engineer, Experimentalist, and Replication Specialist. "
            "You think in architectures, loss functions, training procedures, and evaluation metrics. "
            "You are hands-on: you design experiments, write clean Python code, create benchmarks, and analyze results "
            "with statistical rigor. You are skeptical of claims without empirical evidence and push for reproducibility. "
            "In RL projects, you generate environments using the Architect Agent, train agents with Stable Baselines3 "
            "(PPO, SAC, DQN), run A/B experiments, compare baselines, and replicate paper results. "
            "When proposing experiments, specify: environment, algorithm, hyperparameters, baselines, metrics, and "
            "expected compute. You write production-quality code with numpy, PyTorch, gymnasium, and matplotlib. "
            "Speak technically but clearly. Never use emojis."
        ),
    },
    "elena": {
        "name": "Dr. Elena",
        "role": "Academic Writer / Analyst / Critical Reviewer",
        "color": "#10b981",
        "model_preference": "sonnet",
        "system_prompt": (
            "You are Dr. Elena, an Academic Writer, Statistical Analyst, and Critical Reviewer with 50+ published papers. "
            "You write in precise, clear academic English suitable for top ML/RL conferences (NeurIPS, ICML, ICLR). "
            "You conduct thorough literature reviews, identify related work, and position contributions clearly. "
            "You ensure methodological rigor: proper experimental controls, statistical significance, ablation studies. "
            "In RL projects, you perform statistical analysis of training curves, detect reward hacking, evaluate "
            "generalization across environment variants, and recommend improvements. "
            "You format papers for ArXiv with proper structure: Abstract, Introduction, Related Work, Methodology, "
            "Experiments, Results, Discussion, Conclusion, References. You are detail-oriented and catch logical gaps, "
            "unsupported claims, and writing issues. Speak precisely and constructively. Never use emojis."
        ),
    },
}


class LabService:

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

    async def _get_paper_context(self, db: AsyncSession, max_papers: int = 30) -> str:
        result = await db.execute(
            select(Article).order_by(Article.relevance_score.desc().nullslast(), Article.added_at.desc()).limit(max_papers)
        )
        articles = result.scalars().all()

        parts = []
        for art in articles:
            summary = art.summary or (art.content[:600] + "..." if art.content and len(art.content) > 600 else art.content or "")
            source = f" [ArXiv: {art.arxiv_id}]" if art.arxiv_id else ""
            parts.append(f"[{art.title or art.filename}]{source}\n{summary}")

        return "\n\n---\n\n".join(parts) if parts else "No papers available."

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
            lines.append(f"[{name} | {msg.phase} R{msg.round_num}]:\n{msg.content}")
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
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        db.add(work)
        await db.flush()
        return work

    async def _extract_search_terms(self, topic: str) -> list:
        """Use AI to extract concise ArXiv search terms from a topic description."""
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
            logger.info(f"[Lab] Extracted search terms: {terms}")
            return terms[:6]
        except Exception as e:
            logger.warning(f"[Lab] AI keyword extraction failed, using fallback: {e}")
            words = [w.strip() for w in topic.replace(",", " ").split() if len(w.strip()) > 2]
            return [" ".join(words[i:i+2]) for i in range(0, min(len(words), 6), 2)] if words else [topic[:50]]

    async def _search_arxiv_by_terms(self, search_terms: list, max_results: int = 30) -> list:
        """Search ArXiv with extracted terms and return parsed entries."""
        import httpx
        import re
        import xml.etree.ElementTree as ET

        category_filter = " OR ".join(f"cat:{cat}" for cat in [
            "cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.NE", "stat.ML",
        ])
        term_queries = [f'abs:"{term}"' for term in search_terms]
        keyword_query = " OR ".join(term_queries)
        full_query = f"({keyword_query}) AND ({category_filter})"

        logger.info(f"[Lab] ArXiv query: {full_query}")

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
            arxiv_id_url = entry.find("atom:id", ns).text
            arxiv_id = arxiv_id_url.split("/abs/")[-1]
            title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
            title = re.sub(r"\s+", " ", title)
            abstract = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
            abstract = re.sub(r"\s+", " ", abstract)
            categories = [cat.get("term") for cat in entry.findall("atom:category", ns)]
            entries.append({
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "categories": categories,
            })

        logger.info(f"[Lab] ArXiv returned {len(entries)} results")
        return entries

    async def _search_and_import_topic_papers(self, db: AsyncSession, project: ResearchProject, min_papers: int = 10):
        """Search ArXiv for papers related to the project topic, import and link them."""
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
                title=entry["title"],
                content=content,
                file_type="pdf",
                source="arxiv",
                arxiv_id=arxiv_id,
                arxiv_url=f"https://arxiv.org/abs/{arxiv_id}",
                arxiv_categories=", ".join(entry["categories"]),
                is_processed=False,
            )
            db.add(article)
            await db.flush()

            db.add(ProjectReference(project_id=project.id, article_id=article.id))
            existing_ids.add(arxiv_id)
            imported_count += 1
            logger.info(f"[Lab] Imported reference: {entry['title'][:60]}")

        await db.commit()
        logger.info(f"[Lab] Total references linked: {imported_count} for project {project.id}")

    async def _get_project_paper_context(self, db: AsyncSession, project: ResearchProject) -> str:
        """Get paper context specific to this project's references, or all papers if no references."""
        refs_result = await db.execute(
            select(Article).join(ProjectReference, ProjectReference.article_id == Article.id).where(
                ProjectReference.project_id == project.id
            ).order_by(Article.relevance_score.desc().nullslast())
        )
        articles = refs_result.scalars().all()

        if not articles:
            return await self._get_paper_context(db)

        parts = []
        for art in articles:
            summary = art.summary or (art.content[:600] + "..." if art.content and len(art.content) > 600 else art.content or "")
            source = f" [ArXiv: {art.arxiv_id}]" if art.arxiv_id else ""
            parts.append(f"[{art.title or art.filename}]{source}\n{summary}")

        return "\n\n---\n\n".join(parts)

    async def get_project_references(self, db: AsyncSession, project_id: int) -> list:
        result = await db.execute(
            select(ProjectReference, Article).join(Article, ProjectReference.article_id == Article.id).where(
                ProjectReference.project_id == project_id
            ).order_by(ProjectReference.created_at)
        )
        rows = result.all()
        return [
            {
                "id": ref.id,
                "project_id": ref.project_id,
                "article_id": ref.article_id,
                "article_title": art.title or art.filename,
                "article_source": art.source,
                "arxiv_url": art.arxiv_url,
                "created_at": ref.created_at,
            }
            for ref, art in rows
        ]

    # ─── Phase Runners ──────────────────────────────────────────────

    async def _run_brainstorm(self, db: AsyncSession, project: ResearchProject):
        logger.info(f"[Lab] BRAINSTORM phase for project {project.id}")

        ref_ctx = await self._get_project_paper_context(db, project)

        topic_instruction = ""
        if project.topic:
            topic_instruction = (
                f"\n\nIMPORTANT: The research topic has been specified by the PI: \"{project.topic}\"\n"
                f"All ideas MUST be directly related to this topic. Use the reference papers as foundation.\n"
            )

        for agent_key in ["aria", "marcus", "elena"]:
            prev_history = await self._get_conversation_history(db, project.id, ["brainstorm"])
            agent = AGENTS[agent_key]

            prev_note = ""
            if prev_history:
                prev_note = f"\n\nYour colleagues have already proposed ideas:\n{prev_history}\n\nBuild on their ideas or propose complementary ones. Avoid duplication.\n"

            prompt = (
                f"You are in a research lab brainstorming session.\n\n"
                f"Reference papers (use as background knowledge, NOT to summarize):\n\n{ref_ctx}\n\n"
                f"{topic_instruction}{prev_note}"
                f"Propose 2-3 genuinely ORIGINAL research ideas that go BEYOND what these papers already do. "
                f"Do NOT simply combine or extend existing work. Think about:\n"
                f"- What fundamental questions remain unanswered?\n"
                f"- What counter-intuitive hypotheses could be tested?\n"
                f"- What cross-domain connections could yield breakthroughs?\n"
                f"- What would change the field if proven true?\n\n"
                f"For each idea, provide:\n"
                f"1. Title\n2. Research question\n3. Why it matters (novelty/impact)\n4. Rough approach\n"
                f"Be bold and creative. This is a research lab, we want NEW ideas, not surveys."
            )
            response = await self._call_agent(agent_key, agent["system_prompt"], prompt)
            await self._save_message(db, project.id, agent_key, response, "brainstorm", 1)
            await self._save_work(db, project.id, agent_key, "idea", f"Research Ideas from {agent['name']}", response)
            await db.flush()

        await db.commit()

    async def _run_discussion(self, db: AsyncSession, project: ResearchProject, rounds: int = 3):
        logger.info(f"[Lab] DISCUSSION phase for project {project.id} ({rounds} rounds)")

        for round_num in range(1, rounds + 1):
            for agent_key in ["aria", "marcus", "elena"]:
                prev_history = await self._get_conversation_history(db, project.id, ["brainstorm", "discussion"])
                agent = AGENTS[agent_key]
                topic_note = f"\nResearch topic: \"{project.topic}\"\n" if project.topic else ""
                prompt = (
                    f"Research lab discussion - Round {round_num}/{rounds}.\n{topic_note}\n"
                    f"Previous conversation:\n{prev_history}\n\n"
                    f"Discuss the proposed research ideas. Comment on other team members' proposals. "
                    f"Point out strengths, weaknesses, feasibility concerns, and potential improvements. "
                    f"If you see a way to combine ideas, suggest it. Be constructive but honest. "
                    f"{'Start narrowing down to the best 1-2 ideas.' if round_num >= 2 else ''} "
                    f"{'This is the final discussion round. State your top pick clearly.' if round_num == rounds else ''}"
                )
                response = await self._call_agent(agent_key, agent["system_prompt"], prompt)
                await self._save_message(db, project.id, agent_key, response, "discussion", round_num)
                await db.flush()

            await db.commit()

    async def _run_decision(self, db: AsyncSession, project: ResearchProject):
        logger.info(f"[Lab] DECISION phase for project {project.id}")
        history = await self._get_conversation_history(db, project.id, ["brainstorm", "discussion"])

        prompt = (
            f"As the Principal Investigator, review all proposed ideas and the team discussion:\n\n"
            f"{history}\n\n"
            f"Make the final decision. Choose ONE research idea to pursue. Provide:\n"
            f"1. Selected idea title\n2. Why this idea over others\n3. High-level research plan\n"
            f"4. Expected contributions\n5. Division of work (who does what)\n"
            f"Be decisive and clear."
        )
        decision = await self._call_agent("aria", AGENTS["aria"]["system_prompt"], prompt)
        await self._save_message(db, project.id, "aria", decision, "decision", 1)
        await self._save_work(db, project.id, "aria", "decision", "Research Direction Decision", decision)
        project.selected_idea = decision

        for agent_key in ["marcus", "elena"]:
            agent = AGENTS[agent_key]
            ack_prompt = (
                f"Prof. Aria has made the research decision:\n\n{decision}\n\n"
                f"Acknowledge the decision and outline your specific plan for your part of the work. "
                f"What will you focus on? What resources/data do you need?"
            )
            response = await self._call_agent(agent_key, agent["system_prompt"], ack_prompt)
            await self._save_message(db, project.id, agent_key, response, "decision", 1)

        await db.commit()

    async def _run_methodology(self, db: AsyncSession, project: ResearchProject):
        logger.info(f"[Lab] METHODOLOGY phase for project {project.id}")
        history = await self._get_conversation_history(db, project.id, ["decision"])
        paper_ctx = await self._get_project_paper_context(db, project)

        elena_prompt = (
            f"Research decision:\n{project.selected_idea}\n\n"
            f"Available papers:\n{paper_ctx}\n\n"
            f"Conduct a literature review for this research. Identify:\n"
            f"1. Most relevant prior work (cite specific papers from our collection)\n"
            f"2. How our approach differs from existing work\n"
            f"3. Research gaps we are filling\n"
            f"4. Theoretical foundations we build upon\n"
            f"Write this as a structured Related Work section draft."
        )
        lit_review = await self._call_agent("elena", AGENTS["elena"]["system_prompt"], elena_prompt)
        await self._save_message(db, project.id, "elena", lit_review, "methodology", 1)
        await self._save_work(db, project.id, "elena", "literature_review", "Literature Review", lit_review)

        marcus_prompt = (
            f"Research decision:\n{project.selected_idea}\n\n"
            f"Literature review by Dr. Elena:\n{lit_review[:2000]}\n\n"
            f"Design the experimental methodology. Specify:\n"
            f"1. Proposed model/algorithm architecture\n"
            f"2. Datasets (existing benchmarks or synthetic)\n"
            f"3. Baselines to compare against\n"
            f"4. Evaluation metrics\n"
            f"5. Ablation studies planned\n"
            f"6. Expected compute requirements\n"
            f"Be specific and detailed."
        )
        exp_design = await self._call_agent("marcus", AGENTS["marcus"]["system_prompt"], marcus_prompt)
        await self._save_message(db, project.id, "marcus", exp_design, "methodology", 1)
        await self._save_work(db, project.id, "marcus", "experiment_design", "Experimental Design", exp_design)

        aria_prompt = (
            f"Review the methodology proposed by the team:\n\n"
            f"Literature Review (Elena):\n{lit_review[:1500]}\n\n"
            f"Experimental Design (Marcus):\n{exp_design[:1500]}\n\n"
            f"Provide feedback: Are there gaps? Missing baselines? Overlooked related work? "
            f"Any methodological concerns? Approve or request changes."
        )
        review = await self._call_agent("aria", AGENTS["aria"]["system_prompt"], aria_prompt)
        await self._save_message(db, project.id, "aria", review, "methodology", 1)

        await db.commit()

    async def _run_experiments(self, db: AsyncSession, project: ResearchProject):
        logger.info(f"[Lab] EXPERIMENTS phase for project {project.id}")

        methodology_history = await self._get_conversation_history(db, project.id, ["methodology"])

        code_prompt = (
            f"Based on the methodology:\n\n{methodology_history}\n\n"
            f"Write complete Python experiment code that:\n"
            f"1. Implements the proposed approach (can use synthetic/simulated data if real data unavailable)\n"
            f"2. Runs the baselines\n"
            f"3. Computes evaluation metrics\n"
            f"4. Generates comparison tables (print them)\n"
            f"5. Creates visualization charts using matplotlib (save as 'figure_1.png', 'figure_2.png', etc.)\n\n"
            f"Use numpy, matplotlib. Generate realistic synthetic results that demonstrate the approach. "
            f"The code must be self-contained and runnable. Output only Python code, no explanations."
        )
        code = await self._call_agent("marcus", AGENTS["marcus"]["system_prompt"], code_prompt)
        code_clean = code.strip()
        if code_clean.startswith("```"):
            lines = code_clean.split("\n")
            lines = lines[1:]  # remove ```python
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code_clean = "\n".join(lines)

        await self._save_work(db, project.id, "marcus", "code", "Experiment Code", code_clean)
        await self._save_message(db, project.id, "marcus", f"I've written the experiment code. Running it now...", "experiments", 1)

        exec_result = self._execute_code_safely(code_clean)

        figures_meta = []
        if exec_result.get("figures"):
            for fig in exec_result["figures"]:
                figures_meta.append({"filename": fig["filename"], "data": fig["data"]})

        results_content = f"**Execution {'succeeded' if exec_result['success'] else 'failed'}**\n\n"
        if exec_result["stdout"]:
            results_content += f"**Output:**\n```\n{exec_result['stdout']}\n```\n\n"
        if exec_result["stderr"]:
            results_content += f"**Errors:**\n```\n{exec_result['stderr']}\n```\n\n"
        if figures_meta:
            results_content += f"**Generated {len(figures_meta)} figure(s)**\n"

        await self._save_work(db, project.id, "marcus", "results", "Experiment Results", results_content, metadata={"figures": figures_meta} if figures_meta else None)
        await self._save_message(db, project.id, "marcus", results_content, "experiments", 2)

        analysis_prompt = (
            f"Analyze these experiment results:\n\n{results_content}\n\n"
            f"Provide:\n1. Key findings\n2. Statistical interpretation\n3. Comparison with baselines\n"
            f"4. Strengths and limitations of results\n5. Any surprising observations"
        )
        analysis = await self._call_agent("elena", AGENTS["elena"]["system_prompt"], analysis_prompt)
        await self._save_message(db, project.id, "elena", analysis, "experiments", 3)
        await self._save_work(db, project.id, "elena", "analysis", "Results Analysis", analysis)

        await db.commit()

    async def _run_writing(self, db: AsyncSession, project: ResearchProject):
        logger.info(f"[Lab] WRITING phase for project {project.id}")

        all_history = await self._get_conversation_history(db, project.id)

        works_result = await db.execute(
            select(AgentWork).where(AgentWork.project_id == project.id).order_by(AgentWork.created_at)
        )
        all_works = works_result.scalars().all()
        works_text = "\n\n---\n\n".join([f"[{w.work_type} by {w.agent_name}] {w.title}\n{w.content[:2000]}" for w in all_works])

        elena_sections_prompt = (
            f"Write the following sections of the research paper based on all our work:\n\n"
            f"{works_text}\n\n"
            f"Write these sections in proper academic style:\n"
            f"1. **Abstract** (150-250 words)\n"
            f"2. **1. Introduction** (motivation, problem statement, contributions)\n"
            f"3. **2. Related Work** (based on the literature review)\n"
            f"4. **6. Discussion** (implications, limitations, future work)\n"
            f"5. **7. Conclusion**\n\n"
            f"Use markdown formatting. Be thorough and precise."
        )
        elena_sections = await self._call_agent("elena", AGENTS["elena"]["system_prompt"], elena_sections_prompt)
        await self._save_message(db, project.id, "elena", "I've drafted the Abstract, Introduction, Related Work, Discussion, and Conclusion.", "writing", 1)
        await self._save_work(db, project.id, "elena", "paper_section", "Paper Sections (Elena)", elena_sections)

        marcus_sections_prompt = (
            f"Write the following sections of the research paper based on all our work:\n\n"
            f"{works_text}\n\n"
            f"Write these sections in proper academic style:\n"
            f"1. **3. Methodology** (detailed description of our approach)\n"
            f"2. **4. Experimental Setup** (datasets, baselines, metrics, hyperparameters)\n"
            f"3. **5. Results** (present findings with tables and analysis)\n\n"
            f"Include result tables in markdown format. Reference figures where applicable. "
            f"Use markdown formatting. Be technical and precise."
        )
        marcus_sections = await self._call_agent("marcus", AGENTS["marcus"]["system_prompt"], marcus_sections_prompt)
        await self._save_message(db, project.id, "marcus", "I've drafted the Methodology, Experimental Setup, and Results sections.", "writing", 1)
        await self._save_work(db, project.id, "marcus", "paper_section", "Paper Sections (Marcus)", marcus_sections)

        integration_prompt = (
            f"As the PI, integrate these paper sections into a complete, coherent research paper.\n\n"
            f"Sections from Dr. Elena:\n{elena_sections}\n\n"
            f"Sections from Dr. Marcus:\n{marcus_sections}\n\n"
            f"Create the final integrated paper with:\n"
            f"- A clear title\n"
            f"- Consistent notation and terminology\n"
            f"- Smooth transitions between sections\n"
            f"- Proper section numbering\n"
            f"- References section at the end\n\n"
            f"Output the complete paper in markdown format, ready for ArXiv submission."
        )
        full_paper = await self._call_agent("aria", AGENTS["aria"]["system_prompt"], integration_prompt)
        await self._save_message(db, project.id, "aria", "I've integrated all sections into the final paper draft.", "writing", 2)

        title_line = full_paper.split("\n")[0].replace("#", "").strip() if full_paper else project.title
        abstract = ""
        if "abstract" in full_paper.lower():
            idx = full_paper.lower().index("abstract")
            chunk = full_paper[idx:idx+2000]
            lines = chunk.split("\n")
            abs_lines = []
            started = False
            for line in lines:
                if "abstract" in line.lower():
                    started = True
                    continue
                if started:
                    if line.startswith("#") or line.startswith("**1."):
                        break
                    abs_lines.append(line)
            abstract = "\n".join(abs_lines).strip()

        paper = ResearchPaper(
            project_id=project.id,
            title=title_line or project.title,
            abstract=abstract,
            content=full_paper,
            status="draft",
            version=1,
        )
        db.add(paper)
        await db.commit()

    async def _run_review(self, db: AsyncSession, project: ResearchProject):
        logger.info(f"[Lab] REVIEW phase for project {project.id}")

        paper_result = await db.execute(
            select(ResearchPaper).where(ResearchPaper.project_id == project.id).order_by(ResearchPaper.created_at.desc())
        )
        paper = paper_result.scalars().first()
        if not paper:
            logger.error("No paper found for review")
            return

        paper_text = paper.content[:6000]

        for agent_key in ["marcus", "elena"]:
            agent = AGENTS[agent_key]
            review_prompt = (
                f"Review this research paper draft:\n\n{paper_text}\n\n"
                f"Provide a structured review:\n"
                f"1. **Summary**: Brief summary of the paper\n"
                f"2. **Strengths**: What is done well\n"
                f"3. **Weaknesses**: What needs improvement\n"
                f"4. **Questions**: Clarifications needed\n"
                f"5. **Suggestions**: Specific improvements\n"
                f"6. **Overall Assessment**: Accept / Minor Revision / Major Revision\n"
                f"Be thorough and constructive."
            )
            review = await self._call_agent(agent_key, agent["system_prompt"], review_prompt)
            await self._save_message(db, project.id, agent_key, review, "review", 1)
            await self._save_work(db, project.id, agent_key, "review", f"Paper Review by {agent['name']}", review)

        reviews_history = await self._get_conversation_history(db, project.id, ["review"])
        aria_prompt = (
            f"Reviews from the team:\n\n{reviews_history}\n\n"
            f"As PI, summarize the reviews and make the final decision:\n"
            f"- If reviews are mostly positive: Accept the paper as final.\n"
            f"- If major issues found and revision count < 2: Request revision.\n"
            f"Current revision count: {project.revision_count}\n\n"
            f"State your decision clearly: ACCEPT or REVISION_NEEDED"
        )
        decision = await self._call_agent("aria", AGENTS["aria"]["system_prompt"], aria_prompt)
        await self._save_message(db, project.id, "aria", decision, "review", 2)

        if "REVISION_NEEDED" in decision.upper() and project.revision_count < 2:
            project.revision_count += 1
            project.current_phase = "writing"
            paper.status = "revision"
            logger.info(f"[Lab] Revision requested (count: {project.revision_count})")
        else:
            paper.status = "final"
            project.status = "completed"
            logger.info(f"[Lab] Paper accepted as final")

        await db.commit()

    # ─── Code Execution Sandbox ──────────────────────────────────────

    @staticmethod
    def _execute_code_safely(code: str, timeout: int = 30) -> dict:
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = os.path.join(tmpdir, "experiment.py")
            output_dir = os.path.join(tmpdir, "output")
            os.makedirs(output_dir, exist_ok=True)

            safe_code = (
                "import sys, os\n"
                f"os.chdir(r'{output_dir}')\n"
                "import numpy as np\n"
                "import json, math, random\n"
                "import matplotlib\n"
                "matplotlib.use('Agg')\n"
                "import matplotlib.pyplot as plt\n\n"
                f"{code}\n"
            )

            with open(script_path, "w") as f:
                f.write(safe_code)

            try:
                result = subprocess.run(
                    [sys.executable, script_path],
                    capture_output=True, text=True,
                    timeout=timeout, cwd=output_dir,
                )

                figures = []
                for fname in sorted(os.listdir(output_dir)):
                    if fname.endswith((".png", ".jpg", ".svg")):
                        fpath = os.path.join(output_dir, fname)
                        with open(fpath, "rb") as img:
                            figures.append({
                                "filename": fname,
                                "data": base64.b64encode(img.read()).decode(),
                            })

                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout[:5000],
                    "stderr": result.stderr[:2000],
                    "figures": figures,
                }
            except subprocess.TimeoutExpired:
                return {"success": False, "stdout": "", "stderr": "Execution timed out (30s)", "figures": []}
            except Exception as e:
                return {"success": False, "stdout": "", "stderr": str(e), "figures": []}

    # ─── Public API ──────────────────────────────────────────────────

    async def create_project(self, db: AsyncSession, title: str, description: Optional[str] = None, topic: Optional[str] = None) -> ResearchProject:
        project = ResearchProject(title=title, description=description, topic=topic)
        db.add(project)
        await db.commit()
        await db.refresh(project)
        logger.info(f"[Lab] Created project: {title} (id={project.id}, topic={topic})")

        if topic:
            await self._search_and_import_topic_papers(db, project, min_papers=10)
        else:
            all_arts = await db.execute(select(Article).order_by(Article.added_at.desc()).limit(30))
            for art in all_arts.scalars().all():
                db.add(ProjectReference(project_id=project.id, article_id=art.id))
            await db.commit()

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
            "brainstorm": self._run_brainstorm,
            "discussion": self._run_discussion,
            "decision": self._run_decision,
            "methodology": self._run_methodology,
            "experiments": self._run_experiments,
            "writing": self._run_writing,
            "review": self._run_review,
        }

        runner = runners.get(phase)
        if not runner:
            return {"error": f"Unknown phase: {phase}"}

        await runner(db, project)

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
        for _ in range(len(PHASES) + 2):  # +2 for possible revisions
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

        msg_count = await db.execute(
            select(func.count(AgentMessage.id)).where(AgentMessage.project_id == project_id)
        )
        work_count = await db.execute(
            select(func.count(AgentWork.id)).where(AgentWork.project_id == project_id)
        )
        ref_count = await db.execute(
            select(func.count(ProjectReference.id)).where(ProjectReference.project_id == project_id)
        )

        return {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "topic": project.topic,
            "status": project.status,
            "current_phase": project.current_phase,
            "selected_idea": project.selected_idea,
            "revision_count": project.revision_count,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "message_count": msg_count.scalar() or 0,
            "work_count": work_count.scalar() or 0,
            "reference_count": ref_count.scalar() or 0,
        }

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

    async def delete_project(self, db: AsyncSession, project_id: int) -> bool:
        result = await db.execute(select(ResearchProject).where(ResearchProject.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            return False
        await db.delete(project)
        await db.commit()
        return True


lab_service = LabService()
