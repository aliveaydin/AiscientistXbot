from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(500), nullable=False)
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    file_type = Column(String(50), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    is_processed = Column(Boolean, default=False)

    tweets = relationship("Tweet", back_populates="article")


class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True, index=True)
    tweet_id = Column(String(100), nullable=True, unique=True)
    content = Column(Text, nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=True)
    ai_model_used = Column(String(50), nullable=False)
    status = Column(String(50), default="draft")  # draft, queued, posted, failed
    retry_count = Column(Integer, default=0)
    posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Engagement metrics
    likes = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    replies_count = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    bookmarks = Column(Integer, default=0)

    article = relationship("Article", back_populates="tweets")
    replies = relationship("Reply", back_populates="tweet")


class Reply(Base):
    __tablename__ = "replies"

    id = Column(Integer, primary_key=True, index=True)
    reply_id = Column(String(100), nullable=True, unique=True)
    tweet_id = Column(Integer, ForeignKey("tweets.id"), nullable=False)
    incoming_text = Column(Text, nullable=False)
    incoming_user = Column(String(200), nullable=False)
    incoming_reply_id = Column(String(100), nullable=True)
    response_text = Column(Text, nullable=True)
    ai_model_used = Column(String(50), nullable=True)
    status = Column(String(50), default="pending")  # pending, replied, failed, skipped
    created_at = Column(DateTime, default=datetime.utcnow)
    replied_at = Column(DateTime, nullable=True)

    tweet = relationship("Tweet", back_populates="replies")


class BotSettings(Base):
    __tablename__ = "bot_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(200), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(200), nullable=False)
    details = Column(Text, nullable=True)
    status = Column(String(50), default="info")  # info, success, warning, error
    created_at = Column(DateTime, default=datetime.utcnow)
