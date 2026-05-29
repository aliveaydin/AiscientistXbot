"""
Agent Registry — central registry of all AI agents in the kualia.ai platform.
Provides profile data, prompt inspection, and runtime configuration.
"""
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

OVERRIDES_PATH = os.path.join(os.getenv("DATA_DIR", "/app/data"), "agent_param_overrides.json")

logger = logging.getLogger("agent_registry")


@dataclass
class AgentParam:
    key: str
    label: str
    value: Any
    type: str = "text"  # text, number, select, toggle
    options: Optional[List[str]] = None
    description: str = ""


@dataclass
class AgentProfile:
    id: str
    name: str
    role: str
    avatar_emoji: str
    color: str
    service_file: str
    status: str = "active"
    description: str = ""
    skills: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    models: List[str] = field(default_factory=list)
    scheduled_jobs: List[str] = field(default_factory=list)
    prompts: Dict[str, str] = field(default_factory=dict)
    params: List[AgentParam] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)


class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, AgentProfile] = {}
        self._prompt_overrides: Dict[str, Dict[str, str]] = {}
        self._param_overrides: Dict[str, Dict[str, Any]] = {}
        self._register_all()

    def _register_all(self):
        self._register_science_bot()
        self._register_gtm_strategist()
        self._register_gtm_content()
        self._register_engagement()
        self._register_architect()
        self._register_sage()
        self._register_atlas()
        self._register_arxiv_curator()
        self._register_visual_engine()
        self._register_paper_parser()
        self._register_feedback_analyst()
        self._register_email_marketing()

    def _register_science_bot(self):
        self._agents["science_bot"] = AgentProfile(
            id="science_bot",
            name="ScienceBot",
            role="AI Research Communicator",
            avatar_emoji="🧬",
            color="#3b82f6",
            service_file="ai_service.py + scheduler_service.py",
            description="Autonomous science communicator that reads AI/ML papers, generates insightful tweets, writes blog posts, and builds an engaged research audience on Twitter/X.",
            skills=[
                "Read and analyze AI/ML papers",
                "Generate research-grade tweets",
                "Write in-depth blog articles",
                "Create Twitter threads",
                "Reply to mentions intelligently",
                "Translate content to Turkish",
            ],
            tools=["Twitter API v2 (post, reply, like)", "ArXiv paper feed", "Blog CMS"],
            models=["Claude Sonnet 4.6", "Kimi K2.5", "GPT-4"],
            scheduled_jobs=["tweet_job (every 2h)", "retry_job (every 30m)"],
            prompts={
                "tweet_system": "TWEET_SYSTEM_PROMPT",
                "reply_system": "REPLY_SYSTEM_PROMPT",
                "blog_system": "BLOG_EN_SYSTEM_PROMPT",
                "thread_system": "THREAD_SYSTEM_PROMPT",
            },
            params=[
                AgentParam("tweet_interval", "Tweet Interval (min)", 320, "number", description="Minutes between auto-tweets"),
                AgentParam("auto_reply", "Auto Reply", True, "toggle", description="Reply to mentions automatically"),
                AgentParam("auto_publish_blog", "Auto Publish Blog", True, "toggle", description="Publish blog posts immediately"),
            ],
        )

    def _register_gtm_strategist(self):
        self._agents["gtm_strategist"] = AgentProfile(
            id="gtm_strategist",
            name="GTM Strategist",
            role="Go-to-Market Strategy Director",
            avatar_emoji="🧠",
            color="#8b5cf6",
            service_file="strategy_engine.py",
            description="The strategic brain of kualia.ai's marketing. Creates, evaluates, and pivots GTM strategies autonomously. Decides what content to publish, who to engage, and tracks KPIs.",
            skills=[
                "Create comprehensive GTM strategies",
                "Decide optimal content type & topic per tweet",
                "Select engagement targets & search queries",
                "Weekly strategy review & adjustment",
                "KPI tracking & performance analysis",
                "Autonomous strategy pivoting",
            ],
            tools=["Strategy DB (GTMStrategy, GTMDecisionLog)", "KPI Dashboard", "Tweet & Engagement analytics"],
            models=["Claude Sonnet 4.6", "Kimi K2.5", "GPT-4"],
            scheduled_jobs=["gtm_tweet_job (content decisions, 8h)", "gtm_evaluation_job (weekly review, 168h)"],
            prompts={
                "create_strategy": "CREATE_STRATEGY_PROMPT",
                "decide_content": "DECIDE_CONTENT_PROMPT",
                "decide_engagement": "DECIDE_ENGAGEMENT_PROMPT",
                "review_strategy": "REVIEW_STRATEGY_PROMPT",
            },
            params=[
                AgentParam("review_interval_hours", "Review Interval (hours)", 168, "number", description="Hours between strategy reviews"),
                AgentParam("max_engagement_sessions", "Max Engagement Sessions/Day", 2, "number", description="Maximum engagement runs per day"),
            ],
        )

    def _register_gtm_content(self):
        self._agents["gtm_content"] = AgentProfile(
            id="gtm_content",
            name="GTM Content",
            role="Marketing Content Creator",
            avatar_emoji="📣",
            color="#f59e0b",
            service_file="gtm_service.py",
            description="Creates marketing tweets for kualia.ai across different content categories — product features, industry insights, educational RL content, and platform showcases.",
            skills=[
                "Write product feature tweets",
                "Create industry insight posts",
                "Produce educational RL content",
                "Showcase platform results with data",
                "Generate content calendar",
                "Evaluate marketing performance",
            ],
            tools=["MarketingTweet DB", "Content Calendar", "Visual Engine integration"],
            models=["Claude Sonnet 4.6", "Kimi K2.5", "GPT-4"],
            scheduled_jobs=["gtm_tweet_job (every 8h)", "showcase_job (daily)"],
            prompts={
                "product": "PRODUCT_SYSTEM_PROMPT",
                "industry": "INDUSTRY_SYSTEM_PROMPT",
                "educational": "EDUCATIONAL_SYSTEM_PROMPT",
                "showcase": "SHOWCASE_SYSTEM_PROMPT",
                "evaluation": "EVAL_SYSTEM_PROMPT",
            },
            params=[
                AgentParam("tweet_interval_hours", "Tweet Interval (hours)", 8, "number", description="Hours between GTM tweets"),
                AgentParam("max_tweet_length", "Max Tweet Length", 600, "number", description="Character limit for generated tweets"),
                AgentParam("daily_tweets", "Daily Tweets Target", 3, "number"),
            ],
        )

    def _register_engagement(self):
        self._agents["engagement"] = AgentProfile(
            id="engagement",
            name="Engagement Agent",
            role="Community Engagement Specialist",
            avatar_emoji="🤝",
            color="#ec4899",
            service_file="engagement_service.py",
            description="Finds potential users in the RL/ML community, scores and qualifies prospects, generates value-adding replies, and manages the engagement funnel from discovery to conversion.",
            skills=[
                "Discover potential users on Twitter",
                "Score and qualify prospects with AI",
                "Generate value-adding reply suggestions",
                "Strategic liking of relevant tweets",
                "Manage prospect funnel pipeline",
                "Quote tweet generation",
            ],
            tools=["Twitter Search API", "Prospect DB", "EngagementLog DB", "Kualia Twitter API (like, reply)"],
            models=["Claude Sonnet 4.6", "Kimi K2.5", "GPT-4"],
            scheduled_jobs=["Within gtm_tweet_job (max 2x/day)"],
            prompts={
                "prospect_scorer": "PROSPECT_SCORER_PROMPT",
                "value_reply": "VALUE_REPLY_PROMPT",
                "quote_tweet": "QUOTE_TWEET_PROMPT",
            },
            params=[
                AgentParam("daily_like_limit", "Daily Like Limit", 30, "number", description="Max likes per day"),
                AgentParam("daily_reply_limit", "Daily Reply Limit", 4, "number", description="Max AI reply suggestions per day"),
                AgentParam("max_likes_per_user", "Max Likes Per User/Day", 2, "number"),
            ],
        )

    def _register_architect(self):
        self._agents["architect"] = AgentProfile(
            id="architect",
            name="Architect",
            role="RL Environment Engineer",
            avatar_emoji="🏗️",
            color="#22c55e",
            service_file="architect_service.py",
            description="Designs and generates custom Gymnasium-compatible RL environment code from natural language descriptions. Handles iterative fixing, domain classification, and code validation.",
            skills=[
                "Generate RL environment Python code",
                "Domain classification (robotics, games, finance, etc.)",
                "Iterative code fixing from test errors",
                "Environment specification generation",
                "Paper-to-environment conversion",
                "Custom hypothesis integration into env design",
            ],
            tools=["Sandbox Runner (pytest)", "Code generation", "Domain classifiers"],
            models=["Kimi K2.5", "Claude Sonnet 4.6", "GPT-4"],
            scheduled_jobs=[],
            prompts={
                "architect_system": "ARCHITECT_SYSTEM_PROMPT",
                "spec_generation": "SPEC_GENERATION_PROMPT",
            },
            params=[
                AgentParam("max_fix_iterations", "Max Fix Iterations", 5, "number", description="Max code fix attempts per generation"),
                AgentParam("max_tokens", "Max Tokens", 8192, "number"),
            ],
        )

    def _register_sage(self):
        self._agents["sage"] = AgentProfile(
            id="sage",
            name="Sage",
            role="Research Strategist",
            avatar_emoji="📚",
            color="#6366f1",
            service_file="lab_service.py",
            description="World-class AI Research Strategist in the Research Lab. Formulates hypotheses, designs experiments, analyzes results, conducts literature reviews, and writes academic papers.",
            skills=[
                "Formulate research hypotheses",
                "Design experiment methodology",
                "Analyze training results",
                "Write academic papers with figures",
                "Literature review via ArXiv",
                "Peer review research output",
            ],
            tools=["ArXiv Search API", "Research Paper DB", "Training data analysis", "PDF generation"],
            models=["Kimi K2.5", "Claude Sonnet 4.6", "GPT-4"],
            scheduled_jobs=[],
            prompts={
                "sage_system": "SAGE_SYSTEM_PROMPT",
            },
            params=[
                AgentParam("max_tokens", "Max Tokens", 16000, "number"),
                AgentParam("min_arxiv_papers", "Min ArXiv Papers", 5, "number", description="Minimum papers to fetch for literature review"),
            ],
        )

    def _register_atlas(self):
        self._agents["atlas"] = AgentProfile(
            id="atlas",
            name="Atlas",
            role="RL Training Engineer",
            avatar_emoji="⚡",
            color="#f97316",
            service_file="lab_service.py",
            description="Expert RL Engineer in the Research Lab. Builds environments using Architect, runs training with configurable algorithms and hyperparameters, and feeds results back to Sage for analysis.",
            skills=[
                "Orchestrate environment generation",
                "Configure and run RL training",
                "Monitor training progress",
                "Evaluate trained agents",
                "Select optimal algorithms",
                "Tune hyperparameters",
            ],
            tools=["Architect Service", "Training Service", "Sandbox Runner", "SB3 (PPO/SAC/DQN/A2C/TD3)"],
            models=["Kimi K2.5", "Claude Sonnet 4.6", "GPT-4"],
            scheduled_jobs=[],
            prompts={
                "atlas_system": "ATLAS_SYSTEM_PROMPT",
            },
            params=[
                AgentParam("default_timesteps", "Default Timesteps", 50000, "number"),
                AgentParam("max_env_gen_loops", "Max Env Gen Loops", 3, "number"),
                AgentParam("training_timeout_sec", "Training Timeout (sec)", 1200, "number"),
            ],
        )

    def _register_arxiv_curator(self):
        self._agents["arxiv_curator"] = AgentProfile(
            id="arxiv_curator",
            name="ArXiv Curator",
            role="Paper Discovery & Scoring",
            avatar_emoji="🔬",
            color="#14b8a6",
            service_file="arxiv_service.py",
            description="Automatically discovers and scores new AI/ML/RL papers from ArXiv. Filters by relevance using AI scoring, imports top papers, and feeds them to ScienceBot for tweet generation.",
            skills=[
                "Fetch latest ArXiv papers",
                "AI-based relevance scoring",
                "PDF download and parsing",
                "Classic paper discovery",
                "Feed paper pipeline to tweet bot",
            ],
            tools=["ArXiv Atom API", "PDF parser", "Article DB"],
            models=["Claude Sonnet 4.6", "Kimi K2.5", "GPT-4"],
            scheduled_jobs=["arxiv_job (every 12h)", "classics_job (daily)"],
            prompts={
                "relevance_scorer": "RELEVANCE_PROMPT",
            },
            params=[
                AgentParam("max_papers_per_fetch", "Max Papers/Fetch", 6, "number"),
                AgentParam("min_relevance_score", "Min Relevance Score", 6.0, "number"),
                AgentParam("classic_min_score", "Classic Min Score", 7.0, "number"),
            ],
        )

    def _register_visual_engine(self):
        self._agents["visual_engine"] = AgentProfile(
            id="visual_engine",
            name="Visual Designer",
            role="AI Graphic Designer & Visual Engine",
            avatar_emoji="🎨",
            color="#a855f7",
            service_file="visual_engine.py",
            description="AI-powered graphic designer that creates marketing visuals for tweets. Designs custom HTML/CSS diagrams, flow charts, infographics, training curves, and comparison visuals using LLM, then renders them to PNG via headless Chromium. Also captures site screenshots. White background, clean design.",
            skills=[
                "AI-designed flow diagrams and process visuals",
                "Comparison tables and feature matrices",
                "Training curve and metrics charts (SVG)",
                "Architecture and system diagrams",
                "Step-by-step tutorial visuals",
                "Data-driven infographics",
                "Site screenshot capture",
                "Static template rendering (feature card, stats, code)",
            ],
            tools=["Playwright (headless Chromium)", "LLM (HTML/CSS generation)", "Site screenshot via Playwright navigation"],
            models=["Claude Sonnet 4.6", "Kimi K2.5", "GPT-4"],
            scheduled_jobs=["gtm_tweet_job (1 in 3 tweets)", "showcase_job (daily)"],
            prompts={
                "visual_designer": "VISUAL_DESIGNER_PROMPT",
            },
            params=[
                AgentParam("viewport_width", "Viewport Width", 1200, "number"),
                AgentParam("viewport_height", "Viewport Height", 675, "number"),
                AgentParam("visual_frequency", "Visual Tweet Ratio", "1 in 3", "text", description="How often tweets include visuals"),
            ],
        )

    def _register_paper_parser(self):
        self._agents["paper_parser"] = AgentProfile(
            id="paper_parser",
            name="Paper Parser",
            role="PDF-to-Environment Converter",
            avatar_emoji="📄",
            color="#64748b",
            service_file="paper_parser.py",
            description="Reads research papers (PDF/text) and extracts RL environment specifications. Converts academic descriptions into actionable environment code through Architect.",
            skills=[
                "Extract env specs from papers",
                "Parse observation/action/reward definitions",
                "Map paper concepts to Gymnasium API",
                "Trigger environment generation from specs",
            ],
            tools=["Architect Service", "Sandbox Runner", "PDF text extraction"],
            models=["Kimi K2.5", "Claude Sonnet 4.6", "GPT-4"],
            scheduled_jobs=[],
            prompts={
                "env_extraction": "ENV_EXTRACTION_PROMPT",
            },
            params=[
                AgentParam("max_text_length", "Max Text Length", 12000, "number", description="Truncation limit for paper text"),
            ],
        )

    def _register_feedback_analyst(self):
        self._agents["feedback_analyst"] = AgentProfile(
            id="feedback_analyst",
            name="Feedback Analyst",
            role="Product Feedback Intelligence Agent",
            avatar_emoji="📋",
            color="#f59e0b",
            service_file="routes/feedback.py",
            description="Analyzes every incoming user feedback in real-time. Classifies type (bug, feature request, UX issue), assigns priority based on user impact, detects sentiment, and generates actionable next steps for the development team. Identifies duplicate reports and trend patterns.",
            skills=[
                "Auto-classify feedback (bug, feature, UX, performance, docs, pricing)",
                "Assign priority by user impact (critical → low)",
                "Detect user sentiment and frustration level",
                "Generate concise summaries from verbose reports",
                "Suggest concrete development actions",
                "Flag potential duplicate submissions",
                "Identify trending issues across multiple reports",
            ],
            tools=["LLM (classification & analysis)", "Feedback database"],
            models=["Kimi K2.5", "Claude Sonnet 4.6", "GPT-4"],
            scheduled_jobs=[],
            prompts={
                "analyze": "ANALYZE_SYSTEM_PROMPT",
            },
            params=[
                AgentParam("auto_analyze", "Auto Analyze", True, "toggle", description="Automatically analyze new feedback on submission"),
                AgentParam("auto_priority", "Auto Assign Priority", True, "toggle", description="Let AI assign priority to new feedback"),
            ],
        )

    def _register_email_marketing(self):
        self._agents["email_marketing"] = AgentProfile(
            id="email_marketing",
            name="Email Marketing Agent",
            role="Autonomous Email Campaign Manager",
            avatar_emoji="📧",
            color="#8b5cf6",
            service_file="services/email_marketing_service.py",
            description="Plans, writes, sends, and evaluates marketing email campaigns. Generates weekly RL tips, feature announcements, and re-engagement flows. Tracks delivery metrics, decides target audiences, and adjusts strategy based on performance data.",
            skills=[
                "Generate weekly RL tip emails with AI",
                "Write feature announcement campaigns",
                "Detect and re-engage inactive users (7+ day absence)",
                "Target audience segmentation (plan, activity level)",
                "Track delivery metrics (sent, failed, by template)",
                "Evaluate campaign performance and recommend next actions",
                "Auto-schedule campaigns at optimal intervals",
                "Respect user unsubscribe / marketing opt-out preferences",
            ],
            tools=["Resend API (email delivery)", "LLM (content generation)", "User database (segmentation)", "Campaign database (tracking)"],
            models=["Kimi K2.5", "Claude Sonnet 4.6", "GPT-4"],
            scheduled_jobs=[
                "Weekly Tips (every 7 days)",
                "Re-engagement Check (every 3 days)",
                "Performance Evaluation (every 7 days)",
            ],
            prompts={
                "tips": "TIPS_SYSTEM_PROMPT",
                "feature": "FEATURE_SYSTEM_PROMPT",
                "reengagement": "REENGAGEMENT_SYSTEM_PROMPT",
                "evaluation": "CAMPAIGN_EVAL_PROMPT",
            },
            params=[
                AgentParam("auto_tips", "Auto Weekly Tips", True, "toggle", description="Automatically generate and send weekly RL tip emails"),
                AgentParam("auto_reengagement", "Auto Re-engagement", True, "toggle", description="Automatically send re-engagement emails to inactive users"),
                AgentParam("auto_evaluate", "Auto Performance Review", True, "toggle", description="Automatically evaluate campaign performance weekly"),
                AgentParam("reengagement_days", "Inactivity Threshold", 7, "number", description="Days of inactivity before re-engagement email"),
                AgentParam("max_per_run", "Max Emails Per Run", 50, "number", description="Maximum emails sent per campaign run"),
            ],
        )

    def list_agents(self) -> List[Dict]:
        result = []
        for agent in self._agents.values():
            result.append(self._serialize(agent))
        return result

    def get_agent(self, agent_id: str) -> Optional[Dict]:
        agent = self._agents.get(agent_id)
        if not agent:
            return None
        return self._serialize(agent, full=True)

    def _load_overrides(self):
        try:
            if os.path.exists(OVERRIDES_PATH):
                with open(OVERRIDES_PATH, "r") as f:
                    saved = json.load(f)
                for agent_id, params in saved.items():
                    agent = self._agents.get(agent_id)
                    if not agent:
                        continue
                    self._param_overrides[agent_id] = params
                    for p in agent.params:
                        if p.key in params:
                            p.value = params[p.key]
                logger.info("Loaded agent param overrides from %s", OVERRIDES_PATH)
        except Exception as e:
            logger.warning("Failed to load agent overrides: %s", e)

    def _save_overrides(self):
        try:
            os.makedirs(os.path.dirname(OVERRIDES_PATH), exist_ok=True)
            with open(OVERRIDES_PATH, "w") as f:
                json.dump(self._param_overrides, f, indent=2, default=str)
        except Exception as e:
            logger.warning("Failed to save agent overrides: %s", e)

    def update_agent_param(self, agent_id: str, key: str, value: Any) -> bool:
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        for param in agent.params:
            if param.key == key:
                param.value = value
                if agent_id not in self._param_overrides:
                    self._param_overrides[agent_id] = {}
                self._param_overrides[agent_id][key] = value
                self._save_overrides()
                logger.info("Agent %s param %s updated to %s", agent_id, key, value)
                return True
        return False

    def update_agent_status(self, agent_id: str, status: str) -> bool:
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        agent.status = status
        logger.info("Agent %s status changed to %s", agent_id, status)
        return True

    def get_param(self, agent_id: str, key: str, default: Any = None) -> Any:
        overrides = self._param_overrides.get(agent_id, {})
        if key in overrides:
            return overrides[key]
        agent = self._agents.get(agent_id)
        if agent:
            for p in agent.params:
                if p.key == key:
                    return p.value
        return default

    def _serialize(self, agent: AgentProfile, full: bool = False) -> Dict:
        data = {
            "id": agent.id,
            "name": agent.name,
            "role": agent.role,
            "avatar_emoji": agent.avatar_emoji,
            "color": agent.color,
            "status": agent.status,
            "description": agent.description,
            "skills": agent.skills,
            "tools": agent.tools,
            "models": agent.models,
            "scheduled_jobs": agent.scheduled_jobs,
            "params": [
                {"key": p.key, "label": p.label, "value": p.value, "type": p.type, "options": p.options, "description": p.description}
                for p in agent.params
            ],
        }
        if full:
            data["prompts"] = agent.prompts
            data["service_file"] = agent.service_file
        return data


agent_registry = AgentRegistry()
agent_registry._load_overrides()
