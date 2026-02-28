from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


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
    ai_model_used: str
    status: str
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
