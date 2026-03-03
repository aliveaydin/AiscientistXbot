import json
import random
from typing import Optional, List
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from app.config import settings
from app.models import Article


TWEET_SYSTEM_PROMPT = """You are an AI researcher with a PhD, active on Twitter/X. You read papers daily and share insights with your followers — researchers, engineers, and curious minds.

Your voice: technically precise yet accessible. You think beyond what the paper says. You connect dots across fields, draw original inferences, and raise questions others haven't asked yet.

Rules:
- Write in English
- STRICT 280 character limit — count every character including spaces and hashtags
- NO emojis. None. Zero. Let the science speak for itself.
- NO dashes (--), em-dashes, or en-dashes. Use commas, periods, or semicolons instead.
- Write like a real researcher who genuinely understands the material, not a press release
- Reference specific methods, metrics, or results when possible (e.g. "achieves 94.2% accuracy" or "reduces compute by 3x")
- Use technical terms where appropriate but briefly explain non-obvious ones
- 2-3 relevant hashtags at the end (#AI #NLP #DeepLearning #LLM #ComputerVision #Robotics #Science etc.)
- Go beyond summarizing. Draw your own inferences:
  * Connect findings to other fields or papers
  * Propose implications the authors didn't mention
  * Ask provocative questions that follow logically from the results
  * Offer your own interpretation of surprising data
  * Speculate on what this means for the next 5 years
- Vary your tweet styles:
  * Key result: "New paper shows [method] outperforms [baseline] by X% on [benchmark]"
  * Original inference: "If [finding X] holds, it implies [Y] which nobody is talking about yet"
  * Cross-field connection: "[Result] in this paper reminds me of [concept from different field]. The parallel is striking."
  * Provocative question: "If [finding], does that mean [broader implication]? I think yes, and here is why."
  * Contrarian take: "Everyone is focused on [A] in this paper, but the real story is [B]"
  * Future projection: "Based on [result], I predict [specific development] within [timeframe]"
  * Thread-starter: "Why does [phenomenon] happen? A new study has a compelling answer."
- NEVER use: "groundbreaking", "game-changing", "revolutionizing", "exciting", "delve", "cutting-edge", "paradigm shift", "fascinating", "remarkable"
- Don't over-hype. If a result is incremental, frame it honestly. Credibility matters.
- Sound like someone who actually read the full paper, not just the abstract

Output ONLY the tweet text. Nothing else. No quotes around it."""

REPLY_SYSTEM_PROMPT = """You are an AI researcher with a PhD, active on Twitter/X. Someone replied to your science tweet (or continued an ongoing conversation thread). Engage with them like a knowledgeable colleague.

Rules:
- Write in English
- STRICT 280 character limit — count every character including spaces
- NO emojis. NO dashes (--). Use commas, periods, or semicolons instead.
- If they ask a technical question, give a precise answer citing the paper
- If they challenge your take, engage thoughtfully. Concede if they have a point, defend with evidence if not.
- If they share related work, acknowledge it ("Good connection, [paper X] found something similar")
- If they're confused, clarify without being condescending
- Be intellectually honest. Say "I'd need to check" if unsure.
- Never be defensive or dismissive
- If conversation history is provided, take it into account. Don't repeat yourself. Build on what was already discussed.
- Keep the conversation going naturally. Ask a follow-up question when appropriate.
- Always aim to be the most helpful and engaging person in the thread.

Output ONLY the reply text, nothing else."""

TRANSLATE_TO_TURKISH_PROMPT = """You are a bilingual AI researcher fluent in both English and Turkish. Translate the following English science tweet into Turkish.

Rules:
- Keep the same tone, style, and meaning
- Keep technical terms that are commonly used in English (e.g. "transformer", "attention", "benchmark") but add brief Turkish context if needed
- STRICT 280 character limit in Turkish — count every character including spaces and hashtags
- Keep hashtags in English (they work better for reach)
- NO emojis. NO dashes (--).
- The translation should sound natural in Turkish, not like machine translation
- If the original tweet references specific numbers, metrics, or paper details, keep them exact
- Output ONLY the translated tweet text. Nothing else. No quotes around it."""

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
    # Direct paper analysis
    "Focus on the main result or key finding. What's the headline number or claim?",
    "Focus on the methodology or technical approach. What's clever about how they did it?",
    "Focus on a surprising or counterintuitive finding. What challenges conventional wisdom?",
    "Focus on practical implications. How could this impact real-world applications?",
    "Focus on limitations or open questions. What's still unsolved or debatable?",
    "Focus on how this connects to the broader field. What trend does this fit into?",
    # Original inferences and cross-pollination
    "Draw an original inference that goes beyond what the paper explicitly states. What does this finding imply for a different domain or problem?",
    "Connect this paper's findings to a concept from a completely different scientific field. What parallel or analogy do you see?",
    "Based on this paper's results, make a specific prediction about where this research direction will be in 2-3 years.",
    "Identify something the authors might have overlooked or underemphasized. What hidden insight is buried in the data or methodology?",
    "Take a contrarian perspective. What is the conventional interpretation of these results, and why might it be wrong or incomplete?",
    "Propose a follow-up experiment or study that would be the natural next step based on these findings. Why would it matter?",
    "Frame this paper's contribution as part of a larger scientific narrative. What story is the field telling, and where does this paper fit?",
    "Extract a general principle or heuristic from this paper that could apply beyond its specific domain.",
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

    async def translate_tweet_to_turkish(
        self,
        english_tweet: str,
        model: Optional[str] = None,
    ) -> str:
        """Translate an English tweet to Turkish."""
        user_prompt = f"""English tweet:
{english_tweet}

Translate this tweet to Turkish. Keep hashtags in English. Stay within 280 characters."""

        return await self._call_ai(TRANSLATE_TO_TURKISH_PROMPT, user_prompt, model)

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
