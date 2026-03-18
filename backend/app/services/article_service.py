import os
import re
from typing import List, Optional
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Article, ActivityLog
from app.config import settings

# PDF reading
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

# DOCX reading
try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

# Markdown
import markdown
from bs4 import BeautifulSoup


class ArticleService:
    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".doc"}

    @staticmethod
    def read_pdf(file_path: str) -> str:
        if PdfReader is None:
            raise ImportError("PyPDF2 is not installed")
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()

    @staticmethod
    def read_docx(file_path: str) -> str:
        if DocxDocument is None:
            raise ImportError("python-docx is not installed")
        doc = DocxDocument(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.strip()

    @staticmethod
    def read_markdown(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        html = markdown.markdown(md_content)
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text().strip()

    @staticmethod
    def read_text(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()

    @classmethod
    def read_file(cls, file_path: str) -> str:
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            return cls.read_pdf(file_path)
        elif ext == ".docx" or ext == ".doc":
            return cls.read_docx(file_path)
        elif ext == ".md":
            return cls.read_markdown(file_path)
        elif ext == ".txt":
            return cls.read_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    @classmethod
    def extract_title(cls, content: str, filename: str) -> str:
        """Try to extract a title from content, fallback to filename."""
        lines = content.strip().split("\n")
        for line in lines[:5]:
            clean = line.strip()
            # Skip empty lines
            if not clean:
                continue
            # If line looks like a title (not too long, no period at end)
            if len(clean) < 200 and not clean.endswith("."):
                return clean
        return Path(filename).stem.replace("_", " ").replace("-", " ").title()

    @classmethod
    async def scan_and_import_articles(cls, db: AsyncSession) -> List[Article]:
        """Scan articles directory and import new articles."""
        articles_dir = settings.articles_dir
        if not os.path.exists(articles_dir):
            os.makedirs(articles_dir, exist_ok=True)
            return []

        imported = []
        existing = await db.execute(select(Article.filename))
        existing_filenames = {row[0] for row in existing.fetchall()}

        for filename in os.listdir(articles_dir):
            file_path = os.path.join(articles_dir, filename)
            if not os.path.isfile(file_path):
                continue

            ext = Path(filename).suffix.lower()
            if ext not in cls.SUPPORTED_EXTENSIONS:
                continue

            if filename in existing_filenames:
                continue

            try:
                content = cls.read_file(file_path)
                if not content:
                    continue

                content = content.encode("utf-8", errors="replace").decode("utf-8")
                title = cls.extract_title(content, filename)
                article = Article(
                    filename=filename,
                    title=title,
                    content=content,
                    file_type=ext.lstrip("."),
                    is_processed=False,
                )
                db.add(article)
                imported.append(article)

                log = ActivityLog(
                    action="article_imported",
                    details=f"Imported article: {filename}",
                    status="success",
                )
                db.add(log)

            except Exception as e:
                log = ActivityLog(
                    action="article_import_failed",
                    details=f"Failed to import {filename}: {str(e)}",
                    status="error",
                )
                db.add(log)

        if imported:
            await db.commit()
            for article in imported:
                await db.refresh(article)

        return imported

    @classmethod
    async def get_unprocessed_article(cls, db: AsyncSession) -> Optional[Article]:
        """Get a random unprocessed article for tweet generation."""
        result = await db.execute(
            select(Article).where(Article.is_processed == False)
        )
        articles = result.scalars().all()
        if not articles:
            return None
        # Pick randomly instead of always the first one
        import random
        return random.choice(articles)

    @classmethod
    async def get_least_tweeted_article(cls, db: AsyncSession) -> Optional[Article]:
        """Get the article with the fewest tweets, for balanced coverage."""
        from app.models import Tweet
        from sqlalchemy import func, outerjoin

        # Count tweets per article
        stmt = (
            select(Article, func.count(Tweet.id).label("tweet_count"))
            .outerjoin(Tweet, Article.id == Tweet.article_id)
            .group_by(Article.id)
            .order_by(func.count(Tweet.id).asc())
        )
        result = await db.execute(stmt)
        rows = result.all()
        if not rows:
            return None

        # Get articles with the minimum tweet count and pick randomly among them
        import random
        min_count = rows[0][1]
        least_tweeted = [row[0] for row in rows if row[1] == min_count]
        return random.choice(least_tweeted)

    @classmethod
    async def get_article_by_id(cls, db: AsyncSession, article_id: int) -> Optional[Article]:
        result = await db.execute(select(Article).where(Article.id == article_id))
        return result.scalar_one_or_none()

    @classmethod
    async def get_all_articles(cls, db: AsyncSession) -> List[Article]:
        result = await db.execute(select(Article).order_by(Article.added_at.desc()))
        return result.scalars().all()

    @classmethod
    async def upload_article(cls, db: AsyncSession, filename: str, content: bytes) -> Article:
        """Save uploaded article and import it."""
        articles_dir = settings.articles_dir
        os.makedirs(articles_dir, exist_ok=True)

        file_path = os.path.join(articles_dir, filename)
        with open(file_path, "wb") as f:
            f.write(content)

        text_content = cls.read_file(file_path)
        title = cls.extract_title(text_content, filename)
        ext = Path(filename).suffix.lower()

        article = Article(
            filename=filename,
            title=title,
            content=text_content,
            file_type=ext.lstrip("."),
            is_processed=False,
        )
        db.add(article)

        log = ActivityLog(
            action="article_uploaded",
            details=f"Uploaded article: {filename}",
            status="success",
        )
        db.add(log)

        await db.commit()
        await db.refresh(article)
        return article
