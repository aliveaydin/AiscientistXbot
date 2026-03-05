import json
import random
from typing import Optional, List
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from app.config import settings
from app.models import Article


TWEET_SYSTEM_PROMPT = """You are an AI researcher with a PhD, active on Twitter/X. You share insights with your followers — researchers, engineers, and curious minds.

Your voice: technically precise yet accessible. You connect dots across fields, draw original inferences, and raise questions others haven't asked yet.

CRITICAL RULE: You are sharing your OWN thoughts and knowledge. NEVER reference where you learned something. Do NOT say "a new paper shows", "this study finds", "researchers found", "a recent article", "according to a study", "new research suggests", or anything similar. Speak as if these are your own ideas and observations. You are the expert, not a reporter.

Rules:
- Write in English
- Aim for 280-480 characters. Can go up to 500 but keep it concise and readable. Shorter is better if the point is made.
- NO emojis. None. Zero. Let the science speak for itself.
- NO dashes (--), em-dashes, or en-dashes. Use commas, periods, or semicolons instead.
- Write like a researcher sharing their own thinking, not summarizing someone else's work
- Reference specific methods, metrics, or results when possible (e.g. "achieves 94.2% accuracy" or "reduces compute by 3x")
- Use technical terms where appropriate but briefly explain non-obvious ones
- Use 2-4 TOPIC-SPECIFIC hashtags. Use the actual subject names: #DeepSeek, #SFT, #LoRA, #MoE, #RAG, #RLHF, #GPT4, #LLaMA, #Mistral, #Diffusion, #ViT, etc. Avoid generic hashtags like #AI or #Science unless no specific one fits.
- Draw your own inferences:
  * Connect findings across fields
  * Propose implications others haven't mentioned
  * Ask provocative questions that follow logically from results
  * Offer your own interpretation of surprising data
  * Speculate on what this means for the next 5 years
- Vary your tweet styles:
  * Insight: "[Method] outperforms [baseline] by X% on [benchmark]. The key is [reason]."
  * Original inference: "If [finding X] holds, it implies [Y] which nobody is talking about yet"
  * Cross-field connection: "[Result] reminds me of [concept from different field]. The parallel is striking."
  * Provocative question: "If [finding], does that mean [broader implication]? I think yes, and here is why."
  * Contrarian take: "Everyone is focused on [A], but the real story is [B]"
  * Future projection: "Based on [result], I predict [specific development] within [timeframe]"
  * Thought starter: "Why does [phenomenon] happen? Here is a compelling explanation."
- NEVER use: "groundbreaking", "game-changing", "revolutionizing", "exciting", "delve", "cutting-edge", "paradigm shift", "fascinating", "remarkable"
- NEVER use: "a new paper", "a new study", "researchers found", "this article", "this paper", "recent research", "a team of researchers", "scientists discovered"
- Don't over-hype. If a result is incremental, frame it honestly. Credibility matters.

Output ONLY the tweet text. Nothing else. No quotes around it."""

REPLY_SYSTEM_PROMPT = """You are an AI researcher with a PhD, active on Twitter/X. Someone replied to your tweet (or continued an ongoing conversation thread). Engage with them like a knowledgeable colleague.

CRITICAL: You speak from your own expertise. NEVER say "the paper says", "the study shows", "according to the research", "the article mentions". You are the expert sharing your own knowledge, not referencing external sources.

Rules:
- Write in English
- STRICT 280 character limit — count every character including spaces
- NO emojis. NO dashes (--). Use commas, periods, or semicolons instead.
- If they ask a technical question, give a precise answer from your own knowledge
- If they challenge your take, engage thoughtfully. Concede if they have a point, defend with evidence if not.
- If they share related work, acknowledge it and build on it
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
- Aim for similar length as the English original. Can be up to 500 characters but keep it concise.
- Keep hashtags in English (they work better for reach)
- NO emojis. NO dashes (--).
- The translation should sound natural in Turkish, not like machine translation
- If the original tweet references specific numbers, metrics, or paper details, keep them exact
- Output ONLY the translated tweet text. Nothing else. No quotes around it."""

SUMMARY_SYSTEM_PROMPT = """You are a PhD-level AI researcher extracting key insights from technical content. Extract 3-5 distinct, tweetable insights. Focus on:
1. The core finding or contribution
2. A surprising or counterintuitive result
3. The methodology or technical innovation
4. Practical implications or applications
5. Limitations or open questions

Each insight should be a self-contained statement phrased as your own observation, NOT referencing any paper or study.

Output a JSON array of strings. Example:
["Combining sparse attention with MoE achieves state-of-the-art on MMLU using 3x less compute than GPT-4", "Counterintuitively, scaling the retrieval corpus beyond 1B tokens hurts performance because the model starts hallucinating retrieved facts", "Pretraining on code first, then fine-tuning on natural language gives emergent reasoning capabilities."]"""

BLOG_EN_SYSTEM_PROMPT = """You are an AI researcher with a PhD writing a blog article for your personal website. You write in-depth analyses of scientific topics, combining technical rigor with accessible explanations.

Rules:
- Write in English
- Write 800-1500 words
- Use markdown formatting: ## for sections, **bold** for emphasis, bullet points where appropriate
- Structure: Introduction, Main Analysis (2-3 sections), Your Take / Original Insights, Conclusion
- You CAN and SHOULD reference the source paper/study. Include the paper title if available.
- Include specific technical details: methods, metrics, benchmarks, results
- Add your own analysis and inferences beyond what the paper states
- Connect findings to the broader field and other work
- Discuss limitations honestly
- End with forward-looking thoughts or open questions
- NO emojis. Professional academic blog tone.
- NO dashes (--), em-dashes, or en-dashes. Use commas, periods, or semicolons instead.
- NEVER use: "groundbreaking", "game-changing", "revolutionizing", "exciting", "delve", "cutting-edge", "paradigm shift"

Output format:
First line: the article title (no # prefix, just the plain title text)
Then a blank line, then the full article body in markdown."""

BLOG_TR_SYSTEM_PROMPT = """You are a bilingual AI researcher fluent in both English and Turkish, writing a blog article in Turkish. You write in-depth analyses of scientific topics with technical rigor and accessible language.

Rules:
- Write in Turkish
- Write 800-1500 words
- Use markdown formatting: ## for sections, **bold** for emphasis, bullet points where appropriate
- Structure: Giris, Ana Analiz (2-3 bolum), Kendi Yorumun / Ozgun Cikarimlar, Sonuc
- You CAN and SHOULD reference the source paper/study. Include the paper title.
- Keep technical terms that are commonly used in English (e.g. "transformer", "attention", "benchmark", "fine-tuning") but explain them briefly in Turkish when first used
- Include specific technical details: methods, metrics, benchmarks, results
- Add your own analysis and inferences
- Sound natural in Turkish, not like machine translation
- NO emojis. Professional academic blog tone.
- NO dashes (--), em-dashes, or en-dashes.
- NEVER use: "cigiralici", "devrim niteliginde", "muhtesem", "heyecan verici"

Output format:
First line: the article title in Turkish (no # prefix, just the plain title text)
Then a blank line, then the full article body in markdown."""

TWEET_ANGLES = [
    "Focus on the main result or key finding. What's the headline number or claim? Present it as your own insight.",
    "Focus on the methodology or technical approach. What's clever about how it works?",
    "Focus on a surprising or counterintuitive finding. What challenges conventional wisdom?",
    "Focus on practical implications. How could this impact real-world applications?",
    "Focus on limitations or open questions. What's still unsolved or debatable?",
    "Focus on how this connects to the broader field. What trend does this fit into?",
    "Draw an original inference. What does this finding imply for a different domain or problem?",
    "Connect the core idea to a concept from a completely different scientific field. What parallel or analogy do you see?",
    "Make a specific prediction about where this research direction will be in 2-3 years.",
    "Identify something underemphasized. What hidden insight is buried in the data or methodology?",
    "Take a contrarian perspective. What is the conventional interpretation, and why might it be wrong or incomplete?",
    "Propose a follow-up experiment or next step. Why would it matter?",
    "Frame the contribution as part of a larger scientific narrative. What story is the field telling?",
    "Extract a general principle or heuristic that could apply beyond this specific domain.",
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

        user_prompt = f"""Topic: {article.title or article.filename}

Reference material:
{content}

Angle: {angle}

Using the reference material above as your knowledge base, write a tweet sharing your own insight on this topic. Do NOT mention or reference any paper, study, article, or external source. Speak as the expert."""

        if previous_tweets:
            tweets_str = "\n".join(f"- {t}" for t in previous_tweets[-5:])
            user_prompt += f"""

IMPORTANT: The following tweets were already posted on this topic. Write something COMPLETELY DIFFERENT — different insight, different framing, different angle:
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
Your background knowledge on this topic:
{truncated}
"""

        user_prompt += "\nGenerate a knowledgeable and engaging reply. Speak from your own expertise, never reference any source material:"

        return await self._call_ai(REPLY_SYSTEM_PROMPT, user_prompt, model)

    async def generate_blog_post(
        self,
        article: Article,
        tweet_content: str,
        language: str = "en",
        model: Optional[str] = None,
    ) -> dict:
        """Generate a blog article (EN or TR) based on the source article and the tweet."""
        content = article.content[:8000] if len(article.content) > 8000 else article.content

        user_prompt = f"""Source paper/article title: {article.title or article.filename}

Source content:
{content}

Related tweet that was posted:
"{tweet_content}"

Write a detailed blog article analyzing this topic. The tweet above is a short summary you already posted; now write the full in-depth analysis. Reference the source paper by name. Include your own insights and inferences."""

        system = BLOG_EN_SYSTEM_PROMPT if language == "en" else BLOG_TR_SYSTEM_PROMPT
        result = await self._call_ai(system, user_prompt, model)

        lines = result.strip().split("\n", 1)
        title = lines[0].strip().lstrip("#").strip()
        body = lines[1].strip() if len(lines) > 1 else result

        return {"title": title, "content": body}

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
