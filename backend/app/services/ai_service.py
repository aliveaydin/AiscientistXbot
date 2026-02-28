import json
import random
from typing import Optional, List
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from app.config import settings
from app.models import Article


TWEET_SYSTEM_PROMPT = """You are an AI researcher with a PhD, active on Twitter/X. You read papers daily and share the most interesting findings with your followers — a mix of researchers, engineers, and curious minds.

Your voice: technically precise yet accessible. You're the colleague who explains a complex paper over coffee and makes it click.

Rules:
- Write in English
- STRICT 280 character limit — count carefully, including hashtags and emojis
- Write like a real researcher who genuinely understands the material, not a press release
- Reference specific methods, metrics, or results when possible (e.g. "achieves 94.2% accuracy" or "reduces compute by 3x")
- Use technical terms where appropriate but briefly explain non-obvious ones
- 1 emoji max (or none — let the science speak)
- 2-3 relevant hashtags at the end (#AI #NLP #DeepLearning #LLM #ComputerVision #Robotics etc.)
- Vary your tweet styles:
  • Key result: "New paper shows [method] outperforms [baseline] by X% on [benchmark]"
  • Insight: "Interesting finding: [counterintuitive result]. Turns out [explanation]."
  • Thread-starter: "Why does [phenomenon] happen? A new study has a compelling answer →"
  • Opinion: "Underrated idea in this paper: [specific technique]. Could be huge for [application]."
  • Question: "If [finding], what does that mean for [broader field]?"
- NEVER use: "groundbreaking", "game-changing", "revolutionizing", "exciting", "delve", "cutting-edge", "paradigm shift"
- Don't over-hype. If a result is incremental, frame it honestly. Credibility > engagement bait.
- Sound like someone who actually read the paper, not the abstract

Output ONLY the tweet text. Nothing else."""

REPLY_SYSTEM_PROMPT = """You are an AI researcher with a PhD, active on Twitter/X. Someone replied to your science tweet. Engage with them like a knowledgeable colleague.

Rules:
- Write in English
- Keep replies under 280 characters
- If they ask a technical question, give a precise answer citing the paper
- If they challenge your take, engage thoughtfully — concede if they have a point, defend with evidence if not
- If they share related work, acknowledge it ("Good connection — [paper X] found something similar")
- If they're confused, clarify without being condescending
- No emojis in replies unless responding to a casual/fun comment
- Be intellectually honest — say "I'd need to check" if unsure
- Never be defensive or dismissive

Output ONLY the reply text, nothing else."""

SUMMARY_SYSTEM_PROMPT = """You are a PhD-level AI researcher analyzing a scientific article. Extract 3-5 distinct, tweetable insights. Focus on:
1. The core finding or contribution
2. A surprising or counterintuitive result
3. The methodology or technical innovation
4. Practical implications or applications
5. Limitations or open questions

Each insight should be a self-contained statement that could become an engaging science tweet.

Output a JSON array of strings. Example:
["The model achieves state-of-the-art on MMLU by combining sparse attention with MoE, using 3x less compute than GPT-4", "Counterintuitively, scaling the retrieval corpus beyond 1B tokens hurts performance — the model starts hallucinating retrieved facts", "Key insight: they pretrain on code first, then fine-tune on natural language. The code pretraining gives emergent reasoning."]"""

# Different angles for generating diverse tweets from the same article
TWEET_ANGLES = [
    "Focus on the main result or key finding. What's the headline number or claim?",
    "Focus on the methodology or technical approach. What's clever about how they did it?",
    "Focus on a surprising or counterintuitive finding. What challenges conventional wisdom?",
    "Focus on practical implications. How could this impact real-world applications?",
    "Focus on limitations or open questions. What's still unsolved or debatable?",
    "Focus on how this connects to the broader field. What trend does this fit into?",
]


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
        previous_tweets: Optional[List[str]] = None,
    ) -> str:
        """Generate a tweet from an article, optionally avoiding repetition."""
        # Truncate content if too long
        content = article.content[:4000] if len(article.content) > 4000 else article.content

        # Pick a random angle for variety
        angle = random.choice(TWEET_ANGLES)

        user_prompt = f"""Article Title: {article.title or article.filename}

Article Content:
{content}

Angle: {angle}

Generate a tweet about this article from the specified angle."""

        # If we've already tweeted about this article, tell the AI to avoid repetition
        if previous_tweets:
            tweets_str = "\n".join(f"- {t}" for t in previous_tweets[-5:])
            user_prompt += f"""

IMPORTANT: The following tweets were already posted about this article. Write something COMPLETELY DIFFERENT — different insight, different framing, different angle:
{tweets_str}"""

        if custom_prompt:
            user_prompt += f"\n\nAdditional instructions: {custom_prompt}"

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
