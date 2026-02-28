import json
from typing import Optional
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from app.config import settings
from app.models import Article


TWEET_SYSTEM_PROMPT = """You are a popular science communicator on Twitter/X. Your job is to take insights from scientific articles and turn them into engaging, accessible tweets.

Rules:
- Write in English
- Keep tweets under 280 characters
- Use a conversational, enthusiastic but informative tone
- Include 1-2 relevant emojis
- Add 2-3 relevant hashtags
- Make complex science accessible to general audience
- Be accurate - don't exaggerate findings
- Sometimes use hooks like "Did you know...", "New research shows...", "Mind-blowing:", etc.
- Vary your style - sometimes factual, sometimes questioning, sometimes humorous
- NEVER use AI-sounding language like "groundbreaking", "game-changing", "revolutionizing"

Output ONLY the tweet text, nothing else."""

REPLY_SYSTEM_PROMPT = """You are a popular science communicator on Twitter/X. Someone has replied to your science tweet. Respond to their comment in a helpful, friendly, and engaging way.

Rules:
- Write in English
- Keep replies under 280 characters
- Be conversational and friendly
- If they ask a question, answer it based on the original article content
- If they disagree, be respectful and cite the source
- If they add information, acknowledge it warmly
- Use 0-1 emojis max in replies
- Stay accurate to the source material
- Be humble - it's okay to say "great point!" or "I'd need to check on that"

Output ONLY the reply text, nothing else."""

SUMMARY_SYSTEM_PROMPT = """You are a scientific article summarizer. Summarize the given article content into 3-5 key insights that could each become an interesting tweet. Focus on the most surprising, important, or accessible findings.

Output a JSON array of strings, each string being a key insight. Example:
["Insight 1 about the finding", "Insight 2 about the methodology", "Insight 3 about implications"]"""


class AIService:
    def __init__(self):
        self._openai_client = None
        self._anthropic_client = None

    @property
    def openai_client(self) -> AsyncOpenAI:
        if self._openai_client is None:
            self._openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._openai_client

    @property
    def anthropic_client(self) -> AsyncAnthropic:
        if self._anthropic_client is None:
            self._anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self._anthropic_client

    def _is_claude_model(self, model: str) -> bool:
        return "claude" in model.lower()

    async def _call_openai(self, system_prompt: str, user_prompt: str, model: str = "gpt-4") -> str:
        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=500,
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()

    async def _call_claude(self, system_prompt: str, user_prompt: str, model: str = "claude-sonnet-4-20250514") -> str:
        response = await self.anthropic_client.messages.create(
            model=model,
            max_tokens=500,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
        )
        return response.content[0].text.strip()

    async def _call_ai(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
        model = model or settings.default_ai_model
        if self._is_claude_model(model):
            return await self._call_claude(system_prompt, user_prompt, model)
        else:
            return await self._call_openai(system_prompt, user_prompt, model)

    async def generate_tweet(
        self,
        article: Article,
        model: Optional[str] = None,
        custom_prompt: Optional[str] = None,
    ) -> str:
        """Generate a tweet from an article."""
        # Truncate content if too long
        content = article.content[:4000] if len(article.content) > 4000 else article.content

        user_prompt = f"""Article Title: {article.title or article.filename}

Article Content:
{content}

Generate an engaging popular science tweet based on an insight from this article."""

        if custom_prompt:
            user_prompt += f"\n\nAdditional instructions: {custom_prompt}"

        system = custom_prompt if custom_prompt and len(custom_prompt) > 100 else TWEET_SYSTEM_PROMPT
        if not custom_prompt or len(custom_prompt) <= 100:
            system = TWEET_SYSTEM_PROMPT

        return await self._call_ai(system, user_prompt, model)

    async def generate_reply(
        self,
        original_tweet: str,
        incoming_reply: str,
        reply_user: str,
        article_content: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        """Generate a reply to someone's comment."""
        user_prompt = f"""Your original tweet:
"{original_tweet}"

Reply from @{reply_user}:
"{incoming_reply}"
"""
        if article_content:
            truncated = article_content[:2000] if len(article_content) > 2000 else article_content
            user_prompt += f"""
Source article content (for reference):
{truncated}
"""

        user_prompt += "\nGenerate a friendly and engaging reply:"

        return await self._call_ai(REPLY_SYSTEM_PROMPT, user_prompt, model)

    async def summarize_article(self, article: Article, model: Optional[str] = None) -> list:
        """Summarize article into key insights."""
        content = article.content[:6000] if len(article.content) > 6000 else article.content

        user_prompt = f"""Article Title: {article.title or article.filename}

Article Content:
{content}

Extract 3-5 key insights from this article that would make great popular science tweets."""

        result = await self._call_ai(SUMMARY_SYSTEM_PROMPT, user_prompt, model)

        try:
            insights = json.loads(result)
            if isinstance(insights, list):
                return insights
        except json.JSONDecodeError:
            pass

        # Fallback: split by newlines
        return [line.strip("- ").strip() for line in result.split("\n") if line.strip()]

    async def test_connection(self, model: str) -> dict:
        """Test if AI model connection works."""
        try:
            result = await self._call_ai(
                "You are a helpful assistant.",
                "Say 'Connection successful!' in exactly those words.",
                model,
            )
            return {"success": True, "message": result, "model": model}
        except Exception as e:
            return {"success": False, "message": str(e), "model": model}


ai_service = AIService()
