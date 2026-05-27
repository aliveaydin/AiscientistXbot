from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


SUPPORTED_ALGORITHMS = {"PPO", "SAC", "DQN", "A2C", "TD3", "QRDQN"}
SUPPORTED_VARIANT_ROLES = {"treatment", "baseline", "control"}


# --- Article Schemas ---
class ArticleBase(BaseModel):
    filename: str
    title: Optional[str] = None
    file_type: str


class ArticleResponse(ArticleBase):
    id: int
    content: str
    summary: Optional[str] = None
    added_at: datetime
    is_processed: bool

    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    id: int
    filename: str
    title: Optional[str] = None
    file_type: str
    added_at: datetime
    is_processed: bool
    tweet_count: int = 0
    source: str = "manual"
    arxiv_id: Optional[str] = None
    arxiv_url: Optional[str] = None
    relevance_score: Optional[float] = None

    class Config:
        from_attributes = True


# --- Tweet Schemas ---
class TweetCreate(BaseModel):
    content: str
    article_id: Optional[int] = None
    ai_model: str = "gpt-4"


class TweetResponse(BaseModel):
    id: int
    tweet_id: Optional[str] = None
    content: str
    article_id: Optional[int] = None
    article_title: Optional[str] = None
    ai_model_used: str
    status: str
    language: str = "en"
    parent_tweet_db_id: Optional[int] = None
    is_thread: bool = False
    thread_order: Optional[int] = None
    thread_id: Optional[int] = None
    posted_at: Optional[datetime] = None
    created_at: datetime
    likes: int = 0
    retweets: int = 0
    replies_count: int = 0
    impressions: int = 0
    bookmarks: int = 0

    class Config:
        from_attributes = True


# --- Reply Schemas ---
class ReplyResponse(BaseModel):
    id: int
    reply_id: Optional[str] = None
    tweet_id: int
    incoming_text: str
    incoming_user: str
    response_text: Optional[str] = None
    ai_model_used: Optional[str] = None
    status: str
    created_at: datetime
    replied_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Blog Post Schemas ---
class BlogPostResponse(BaseModel):
    id: int
    tweet_id: Optional[int] = None
    article_id: Optional[int] = None
    title: str
    content: str
    language: str = "en"
    ai_model_used: str
    status: str
    created_at: datetime
    tweet_content: Optional[str] = None
    article_title: Optional[str] = None

    class Config:
        from_attributes = True


# --- Settings Schemas ---
class SettingsUpdate(BaseModel):
    default_ai_model: Optional[str] = None
    tweet_interval_minutes: Optional[int] = None
    auto_reply_enabled: Optional[bool] = None
    tweet_style: Optional[str] = None
    reply_style: Optional[str] = None


class SettingsResponse(BaseModel):
    default_ai_model: str
    tweet_interval_minutes: int
    auto_reply_enabled: bool
    tweet_style: str
    reply_style: str
    scheduler_running: bool


# --- Dashboard Schemas ---
class DashboardStats(BaseModel):
    total_tweets: int
    total_replies: int
    total_articles: int
    total_likes: int
    total_retweets: int
    total_impressions: int
    tweets_today: int
    replies_today: int
    avg_engagement_rate: float


class GenerateTweetRequest(BaseModel):
    article_id: Optional[int] = None
    ai_model: str = "gpt-4"
    custom_prompt: Optional[str] = None


class ActivityLogResponse(BaseModel):
    id: int
    action: str
    details: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Research Lab Schemas ---


class EnvVariantConfig(BaseModel):
    """One environment variant in an ablation study.

    `role` controls how the env is interpreted in the final paper:
      - treatment: hypothesis applied
      - baseline:  hypothesis NOT applied (control comparison)
      - control:   any additional ablation variant
    `modifier` is a short instruction injected into the env-generation prompt
    so the underlying environment is otherwise identical to its siblings.
    """
    label: str = Field(..., min_length=1, max_length=200)
    role: str = "treatment"
    modifier: Optional[str] = None

    @field_validator("role")
    @classmethod
    def _validate_role(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in SUPPORTED_VARIANT_ROLES:
            raise ValueError(f"role must be one of {SUPPORTED_VARIANT_ROLES}")
        return v


class HyperparamsConfig(BaseModel):
    learning_rate: Optional[float] = None
    batch_size: Optional[int] = None
    gamma: Optional[float] = None
    net_arch: Optional[str] = None  # "small" | "medium" | "large"


class ExperimentConfig(BaseModel):
    """Advanced settings for a research project."""
    env_variants: List[EnvVariantConfig] = Field(default_factory=list)
    algorithms: List[str] = Field(default_factory=lambda: ["PPO"])
    n_seeds: int = Field(1, ge=1, le=10)
    timesteps: int = Field(50000, ge=1000, le=2_000_000)
    n_eval_episodes: int = Field(10, ge=1, le=100)
    hyperparams: Optional[HyperparamsConfig] = None

    @field_validator("algorithms")
    @classmethod
    def _validate_algorithms(cls, v: List[str]) -> List[str]:
        upper = [a.upper() for a in v if a]
        bad = [a for a in upper if a not in SUPPORTED_ALGORITHMS]
        if bad:
            raise ValueError(f"unsupported algorithms: {bad}. Allowed: {sorted(SUPPORTED_ALGORITHMS)}")
        if not upper:
            return ["PPO"]
        # de-duplicate while preserving order
        seen: List[str] = []
        for a in upper:
            if a not in seen:
                seen.append(a)
        return seen

    @field_validator("env_variants")
    @classmethod
    def _validate_variants(cls, v: List[EnvVariantConfig]) -> List[EnvVariantConfig]:
        # If user supplies variants, ensure unique labels.
        labels = [x.label.strip().lower() for x in v]
        if len(labels) != len(set(labels)):
            raise ValueError("env_variants labels must be unique")
        return v


class ResearchProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    topic: Optional[str] = None
    experiment_config: Optional[ExperimentConfig] = None


class ResearchProjectResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    topic: Optional[str] = None
    status: str
    current_phase: str
    selected_idea: Optional[str] = None
    revision_count: int = 0
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    work_count: int = 0
    reference_count: int = 0

    class Config:
        from_attributes = True


class ProjectReferenceResponse(BaseModel):
    id: int
    project_id: int
    article_id: int
    article_title: Optional[str] = None
    article_source: Optional[str] = None
    arxiv_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AgentMessageResponse(BaseModel):
    id: int
    project_id: int
    agent_name: str
    content: str
    phase: str
    round_num: int
    created_at: datetime

    class Config:
        from_attributes = True


class AgentWorkResponse(BaseModel):
    id: int
    project_id: int
    agent_name: str
    work_type: str
    title: str
    content: str
    metadata_json: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchPaperResponse(BaseModel):
    id: int
    project_id: int
    title: str
    abstract: Optional[str] = None
    content: str
    status: str
    version: int
    created_at: datetime

    class Config:
        from_attributes = True
