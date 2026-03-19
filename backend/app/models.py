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
    source = Column(String(50), default="manual")  # manual, arxiv
    arxiv_id = Column(String(100), nullable=True, unique=True)
    arxiv_url = Column(String(500), nullable=True)
    arxiv_categories = Column(String(500), nullable=True)
    relevance_score = Column(Float, nullable=True)

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
    language = Column(String(10), default="en")  # en, tr
    parent_tweet_db_id = Column(Integer, nullable=True)  # links TR tweet to its EN original
    is_thread = Column(Boolean, default=False)
    thread_order = Column(Integer, nullable=True)  # 0, 1, 2 for tweets in a thread
    thread_id = Column(Integer, nullable=True)  # DB id of the first tweet in the thread
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


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, index=True)
    tweet_id = Column(Integer, ForeignKey("tweets.id"), nullable=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String(10), default="en")
    ai_model_used = Column(String(50), nullable=False)
    status = Column(String(50), default="draft")  # draft, published
    published = Column(Boolean, default=False)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tweet = relationship("Tweet")
    article = relationship("Article")


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


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    clerk_id = Column(String(200), unique=True, nullable=False, index=True)
    email = Column(String(500), nullable=True)
    username = Column(String(200), unique=True, nullable=True, index=True)
    display_name = Column(String(500), nullable=True)
    avatar_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    environments = relationship("RLEnvironment", back_populates="owner", foreign_keys="RLEnvironment.user_id")
    research_projects = relationship("ResearchProject", back_populates="owner", foreign_keys="ResearchProject.user_id")


class ResearchProject(Base):
    __tablename__ = "research_projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    topic = Column(Text, nullable=True)
    status = Column(String(50), default="active")  # active, completed, paused, failed
    current_phase = Column(String(50), default="research")
    selected_idea = Column(Text, nullable=True)
    revision_count = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="research_projects", foreign_keys=[user_id])
    messages = relationship("AgentMessage", back_populates="project", cascade="all, delete-orphan")
    works = relationship("AgentWork", back_populates="project", cascade="all, delete-orphan")
    papers = relationship("ResearchPaper", back_populates="project", cascade="all, delete-orphan")
    references = relationship("ProjectReference", back_populates="project", cascade="all, delete-orphan")
    environments = relationship("RLEnvironment", back_populates="research_project", foreign_keys="RLEnvironment.research_project_id")


class ProjectReference(Base):
    __tablename__ = "project_references"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("research_projects.id"), nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("ResearchProject", back_populates="references")
    article = relationship("Article")


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("research_projects.id"), nullable=False)
    agent_name = Column(String(100), nullable=False)  # aria, marcus, elena
    content = Column(Text, nullable=False)
    phase = Column(String(50), nullable=False)
    round_num = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("ResearchProject", back_populates="messages")


class AgentWork(Base):
    __tablename__ = "agent_works"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("research_projects.id"), nullable=False)
    agent_name = Column(String(100), nullable=False)
    work_type = Column(String(100), nullable=False)  # idea, literature_review, experiment_design, code, results, chart, paper_section, review
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)  # JSON for figures (base64), code output, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("ResearchProject", back_populates="works")


class ResearchPaper(Base):
    __tablename__ = "research_papers"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("research_projects.id"), nullable=False)
    title = Column(String(500), nullable=False)
    abstract = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    status = Column(String(50), default="draft")  # draft, under_review, revision, final
    version = Column(Integer, default=1)
    published = Column(Boolean, default=False)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("ResearchProject", back_populates="papers")


class RLEnvironment(Base):
    __tablename__ = "rl_environments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    slug = Column(String(200), unique=True, nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), default="custom")
    observation_space = Column(Text, nullable=True)
    action_space = Column(Text, nullable=True)
    reward_description = Column(Text, nullable=True)
    code = Column(Text, nullable=True)
    env_spec_json = Column(Text, nullable=True)
    test_results_json = Column(Text, nullable=True)
    preview_image = Column(Text, nullable=True)
    difficulty = Column(String(50), default="medium")
    status = Column(String(50), default="draft")
    ai_model_used = Column(String(50), nullable=True)
    topic = Column(Text, nullable=True)
    version = Column(Integer, default=1)
    generation_log = Column(Text, nullable=True)
    is_template = Column(Boolean, default=False)
    domain = Column(String(100), nullable=True)
    max_steps = Column(Integer, default=1000)
    api_enabled = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    research_project_id = Column(Integer, ForeignKey("research_projects.id"), nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="environments", foreign_keys=[user_id])
    research_project = relationship("ResearchProject", back_populates="environments", foreign_keys=[research_project_id])
    builder_conversations = relationship("BuilderConversation", back_populates="environment", cascade="all, delete-orphan")
    training_runs = relationship("TrainingRun", back_populates="environment", cascade="all, delete-orphan")
    versions = relationship("EnvVersion", back_populates="environment", cascade="all, delete-orphan")


class BuilderConversation(Base):
    __tablename__ = "builder_conversations"

    id = Column(Integer, primary_key=True, index=True)
    env_id = Column(Integer, ForeignKey("rl_environments.id"), nullable=False)
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    version_snapshot = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    environment = relationship("RLEnvironment", back_populates="builder_conversations")


class TrainingRun(Base):
    __tablename__ = "training_runs"

    id = Column(Integer, primary_key=True, index=True)
    env_id = Column(Integer, ForeignKey("rl_environments.id"), nullable=False)
    algorithm = Column(String(50), nullable=False)  # PPO, DQN, SAC
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    config_json = Column(Text, nullable=True)
    results_json = Column(Text, nullable=True)
    model_path = Column(String(500), nullable=True)
    training_curve_json = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    environment = relationship("RLEnvironment", back_populates="training_runs")


class EnvVersion(Base):
    __tablename__ = "env_versions"

    id = Column(Integer, primary_key=True, index=True)
    env_id = Column(Integer, ForeignKey("rl_environments.id"), nullable=False)
    version = Column(Integer, nullable=False)
    code = Column(Text, nullable=True)
    spec_json = Column(Text, nullable=True)
    change_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    environment = relationship("RLEnvironment", back_populates="versions")


class SkillCache(Base):
    __tablename__ = "skill_cache"

    id = Column(Integer, primary_key=True, index=True)
    domain_key = Column(String(200), unique=True, nullable=False)
    skill_prompt = Column(Text, nullable=False)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
