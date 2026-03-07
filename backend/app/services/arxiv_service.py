import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Article, ActivityLog

logger = logging.getLogger("arxiv")

ARXIV_API_URL = "http://export.arxiv.org/api/query"

ARXIV_CATEGORIES = [
    "cs.AI",   # Artificial Intelligence
    "cs.LG",   # Machine Learning
    "cs.CL",   # Computation and Language (NLP/LLM)
    "cs.CV",   # Computer Vision
    "cs.NE",   # Neural and Evolutionary Computing
    "stat.ML", # Statistical Machine Learning
]

RELEVANCE_PROMPT = """You are an AI research curator selecting papers for a popular science Twitter account with a PhD-level audience.

Rate the following paper abstract on a scale of 1-10 for "tweetability" based on:
- Novelty: Is this a new approach or incremental?
- Impact: Could this change how people think about the field?
- Accessibility: Can the core insight be explained in a tweet?
- Buzz factor: Would AI researchers and enthusiasts find this interesting?

Paper title: {title}
Abstract: {abstract}
Categories: {categories}

Respond with ONLY a single number from 1 to 10. Nothing else."""


class ArxivService:

    @staticmethod
    async def fetch_recent_papers(max_results: int = 50) -> List[dict]:
        """Fetch recent papers from ArXiv API."""
        category_query = "+OR+".join(f"cat:{cat}" for cat in ARXIV_CATEGORIES)
        params = {
            "search_query": category_query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": max_results,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(ARXIV_API_URL, params=params)
            response.raise_for_status()

        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        root = ET.fromstring(response.text)
        papers = []

        for entry in root.findall("atom:entry", ns):
            arxiv_id_url = entry.find("atom:id", ns).text
            arxiv_id = arxiv_id_url.split("/abs/")[-1]

            title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
            title = re.sub(r"\s+", " ", title)

            abstract = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
            abstract = re.sub(r"\s+", " ", abstract)

            categories = [
                cat.get("term")
                for cat in entry.findall("atom:category", ns)
            ]

            published = entry.find("atom:published", ns).text
            pdf_link = None
            for link in entry.findall("atom:link", ns):
                if link.get("title") == "pdf":
                    pdf_link = link.get("href")

            authors = [
                author.find("atom:name", ns).text
                for author in entry.findall("atom:author", ns)
            ]

            papers.append({
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "categories": categories,
                "published": published,
                "pdf_url": pdf_link or f"https://arxiv.org/pdf/{arxiv_id}",
                "abs_url": f"https://arxiv.org/abs/{arxiv_id}",
                "authors": authors[:5],
            })

        return papers

    @staticmethod
    async def score_paper(paper: dict) -> float:
        """Use AI to score a paper's relevance/tweetability (1-10)."""
        from app.services.ai_service import ai_service

        prompt = RELEVANCE_PROMPT.format(
            title=paper["title"],
            abstract=paper["abstract"][:2000],
            categories=", ".join(paper["categories"]),
        )

        try:
            result = await ai_service._call_ai(
                "You are a paper relevance scorer. Output only a number.",
                prompt,
            )
            score = float(re.search(r"(\d+(?:\.\d+)?)", result).group(1))
            return min(max(score, 1.0), 10.0)
        except Exception as e:
            logger.warning(f"Failed to score paper '{paper['title'][:50]}': {e}")
            return 5.0

    @staticmethod
    async def download_pdf(pdf_url: str, save_path: str) -> bool:
        """Download a PDF from ArXiv."""
        try:
            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                response = await client.get(pdf_url)
                response.raise_for_status()
                with open(save_path, "wb") as f:
                    f.write(response.content)
            return True
        except Exception as e:
            logger.error(f"Failed to download PDF from {pdf_url}: {e}")
            return False

    @classmethod
    async def fetch_and_import(
        cls,
        db: AsyncSession,
        max_papers: int = 3,
        min_score: float = 6.0,
    ) -> List[Article]:
        """Main pipeline: fetch papers, score them, download top ones, import to DB."""
        logger.info(f"Starting ArXiv fetch (categories: {ARXIV_CATEGORIES})")

        papers = await cls.fetch_recent_papers(max_results=40)
        logger.info(f"Fetched {len(papers)} papers from ArXiv")

        if not papers:
            return []

        existing = await db.execute(select(Article.arxiv_id).where(Article.arxiv_id.isnot(None)))
        existing_ids = {row[0] for row in existing.fetchall()}

        new_papers = [p for p in papers if p["arxiv_id"] not in existing_ids]
        logger.info(f"{len(new_papers)} new papers (filtered {len(papers) - len(new_papers)} duplicates)")

        if not new_papers:
            logger.info("No new papers to process")
            return []

        scored = []
        for paper in new_papers[:15]:
            score = await cls.score_paper(paper)
            paper["score"] = score
            scored.append(paper)
            logger.info(f"  Score {score:.1f}: {paper['title'][:60]}")

        scored.sort(key=lambda p: p["score"], reverse=True)
        top_papers = [p for p in scored if p["score"] >= min_score][:max_papers]

        if not top_papers:
            logger.info(f"No papers scored above {min_score}. Importing top-scored paper as fallback.")
            top_papers = scored[:1]

        imported = []
        import os
        articles_dir = settings.articles_dir
        os.makedirs(articles_dir, exist_ok=True)

        for paper in top_papers:
            filename = f"arxiv_{paper['arxiv_id'].replace('/', '_')}.pdf"
            save_path = os.path.join(articles_dir, filename)

            downloaded = await cls.download_pdf(paper["pdf_url"], save_path)
            if not downloaded:
                continue

            try:
                from app.services.article_service import ArticleService
                content = ArticleService.read_pdf(save_path)
                if not content or len(content) < 100:
                    logger.warning(f"PDF content too short for {paper['arxiv_id']}, using abstract")
                    content = f"{paper['title']}\n\nAbstract:\n{paper['abstract']}"
            except Exception as e:
                logger.warning(f"Failed to parse PDF for {paper['arxiv_id']}: {e}, using abstract")
                content = f"{paper['title']}\n\nAbstract:\n{paper['abstract']}"

            article = Article(
                filename=filename,
                title=paper["title"],
                content=content,
                file_type="pdf",
                source="arxiv",
                arxiv_id=paper["arxiv_id"],
                arxiv_url=paper["abs_url"],
                arxiv_categories=", ".join(paper["categories"]),
                relevance_score=paper["score"],
                is_processed=False,
            )
            db.add(article)
            imported.append(article)

            log = ActivityLog(
                action="arxiv_paper_imported",
                details=f"[ArXiv] Imported: {paper['title'][:80]} (score: {paper['score']:.1f})",
                status="success",
            )
            db.add(log)
            logger.info(f"Imported: {paper['title'][:60]} (score: {paper['score']:.1f})")

        if imported:
            await db.commit()
            for a in imported:
                await db.refresh(a)

        log = ActivityLog(
            action="arxiv_fetch_complete",
            details=f"ArXiv fetch complete: {len(imported)} papers imported from {len(papers)} candidates",
            status="success" if imported else "info",
        )
        db.add(log)
        await db.commit()

        return imported


arxiv_service = ArxivService()
