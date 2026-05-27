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


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # free, starter, pro, lab
    display_name = Column(String(200), nullable=False)
    price_monthly = Column(Float, default=0)
    monthly_credits = Column(Float, default=0)  # USD credits granted monthly
    max_environments = Column(Integer, default=3)  # -1 = unlimited
    max_training_steps = Column(Integer, default=50000)
    pdf_download = Column(Boolean, default=False)
    github_export = Column(Boolean, default=False)
    can_buy_credits = Column(Boolean, default=False)
    features_json = Column(Text, nullable=True)  # extra feature flags
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)  # positive = credit, negative = debit
    balance_after = Column(Float, nullable=False)
    operation = Column(String(100), nullable=False)  # env_generation, builder_chat, training, research_hypothesis, research_experiment, research_paper, paper_from_env, reference_search, monthly_grant, credit_purchase, admin_grant
    resource_id = Column(Integer, nullable=True)  # env_id, project_id, run_id
    details_json = Column(Text, nullable=True)  # {prompt_tokens, completion_tokens, model, actual_cost, ...}
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="credit_transactions")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    clerk_id = Column(String(200), unique=True, nullable=False, index=True)
    email = Column(String(500), nullable=True)
    username = Column(String(200), unique=True, nullable=True, index=True)
    display_name = Column(String(500), nullable=True)
    avatar_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    credit_balance = Column(Float, default=0)  # current USD credits
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=True)
    plan_started_at = Column(DateTime, nullable=True)
    plan_period_end = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String(200), nullable=True)  # for later Stripe integration
    email_notifications = Column(Boolean, default=True)
    marketing_emails = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    plan = relationship("SubscriptionPlan")
    environments = relationship("RLEnvironment", back_populates="owner", foreign_keys="RLEnvironment.user_id")
    research_projects = relationship("ResearchProject", back_populates="owner", foreign_keys="ResearchProject.user_id")
    credit_transactions = relationship("CreditTransaction", back_populates="user", cascade="all, delete-orphan")


class ResearchProject(Base):
    __tablename__ = "research_projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    topic = Column(Text, nullable=True)
    status = Column(String(50), default="active")  # active, completed, paused, failed
    current_phase = Column(String(50), default="hypothesis")
    phase_running = Column(Boolean, default=False)
    selected_idea = Column(Text, nullable=True)
    # User-supplied advanced experiment configuration (env variants, algorithms,
    # n_seeds, timesteps, hyperparams). When NULL, the LLM-driven defaults apply.
    experiment_config_json = Column(Text, nullable=True)
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
    # Ablation/comparison metadata for envs created inside a Research Lab project.
    # variant_role: treatment | baseline | control (None for non-research envs)
    # variant_label: short human-readable tag, e.g. "with self-observation"
    variant_role = Column(String(50), nullable=True)
    variant_label = Column(String(200), nullable=True)
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
    algorithm = Column(String(50), nullable=False)  # PPO, DQN, SAC, A2C, TD3, QRDQN
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    config_json = Column(Text, nullable=True)
    results_json = Column(Text, nullable=True)
    model_path = Column(String(500), nullable=True)
    training_curve_json = Column(Text, nullable=True)
    # Seed used for this run; multiple runs with different seeds let us report
    # mean ± std across runs in the paper's results table.
    seed = Column(Integer, nullable=True)
    # Mirror of the env's variant_role for fast grouping in result aggregation.
    variant_role = Column(String(50), nullable=True)
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


class MarketingTweet(Base):
    __tablename__ = "marketing_tweets"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), nullable=False)  # product, industry, educational, showcase
    ai_model_used = Column(String(50), nullable=True)
    status = Column(String(50), default="draft")  # draft, approved, posted, failed
    tweet_id = Column(String(100), nullable=True, unique=True)
    media_url = Column(Text, nullable=True)  # local path to generated image
    hashtags = Column(Text, nullable=True)
    scheduled_for = Column(DateTime, nullable=True)
    posted_at = Column(DateTime, nullable=True)
    likes = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    replies_count = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class EngagementLog(Base):
    __tablename__ = "engagement_logs"

    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String(50), nullable=False)  # like, reply, follow, quote_reply, prospect_detect
    target_tweet_id = Column(String(100), nullable=True)
    target_username = Column(String(200), nullable=True)
    target_text = Column(Text, nullable=True)
    search_query = Column(String(500), nullable=True)
    reply_suggestion = Column(Text, nullable=True)
    status = Column(String(50), default="completed")  # completed, failed, pending_approval, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)


class GTMReport(Base):
    """Periodic GTM performance evaluation and AI-generated recommendations."""
    __tablename__ = "gtm_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(50), nullable=False)  # weekly, manual
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    metrics_json = Column(Text, nullable=True)
    analysis = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class GTMStrategy(Base):
    """Living strategy document — the brain's current plan."""
    __tablename__ = "gtm_strategies"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(Integer, default=1)
    status = Column(String(30), default="active")  # active, archived
    mission = Column(Text, nullable=False)
    target_audiences = Column(Text, nullable=True)   # JSON array
    kpis = Column(Text, nullable=True)               # JSON array of {name, target, current, unit}
    content_strategy = Column(Text, nullable=True)   # JSON: mix %, tone, focus, topics
    engagement_strategy = Column(Text, nullable=True) # JSON: search focus, reply approach
    weekly_goals = Column(Text, nullable=True)       # JSON array of strings
    constraints = Column(Text, nullable=True)        # JSON: budget, limits
    ai_reasoning = Column(Text, nullable=True)       # why this strategy was chosen
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GTMDecisionLog(Base):
    """Every strategic decision the agent makes, with reasoning."""
    __tablename__ = "gtm_decision_logs"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, nullable=True)
    decision_type = Column(String(50), nullable=False)  # content_choice, engagement_target, strategy_pivot, kpi_review
    context = Column(Text, nullable=True)     # what data the agent saw
    decision = Column(Text, nullable=True)    # what it decided
    reasoning = Column(Text, nullable=True)   # why
    outcome = Column(Text, nullable=True)     # what happened (filled later)
    created_at = Column(DateTime, default=datetime.utcnow)


class Prospect(Base):
    """Potential users detected from Twitter activity."""
    __tablename__ = "prospects"

    id = Column(Integer, primary_key=True, index=True)
    twitter_username = Column(String(200), unique=True, nullable=False, index=True)
    twitter_user_id = Column(String(100), nullable=True)
    display_name = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    score = Column(Integer, default=0)  # 0-100 prospect quality score
    tags = Column(Text, nullable=True)  # JSON: ["researcher", "student", "lab", "industry"]
    stage = Column(String(50), default="detected")  # detected, engaged, warm, converted, disqualified
    first_seen_tweet = Column(Text, nullable=True)
    total_interactions = Column(Integer, default=0)
    last_interaction_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Feedback(Base):
    """User-submitted feedback: bugs, feature requests, questions."""
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_email = Column(String(500), nullable=True)
    user_name = Column(String(500), nullable=True)
    type = Column(String(50), default="general")  # bug, feature, question, general
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    page_url = Column(String(1000), nullable=True)
    status = Column(String(50), default="new")  # new, reviewed, in_progress, resolved, wont_fix
    priority = Column(String(50), nullable=True)  # critical, high, medium, low
    ai_category = Column(String(100), nullable=True)
    ai_summary = Column(Text, nullable=True)
    ai_sentiment = Column(String(50), nullable=True)  # positive, neutral, negative, frustrated
    ai_suggested_action = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="feedback_items", foreign_keys=[user_id])


class EmailLog(Base):
    """Log of every email sent through the platform."""
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    to_email = Column(String(500), nullable=False)
    subject = Column(String(1000), nullable=False)
    template = Column(String(100), nullable=True)
    channel = Column(String(50), default="transactional")  # transactional, marketing
    status = Column(String(50), default="sent")  # sent, failed, bounced
    resend_id = Column(String(200), nullable=True)
    error = Column(Text, nullable=True)
    campaign_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EmailCampaign(Base):
    """AI-generated marketing email campaigns."""
    __tablename__ = "email_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    campaign_type = Column(String(50), nullable=False)  # new_feature, tips_tricks, reengagement, custom
    subject = Column(String(1000), nullable=False)
    headline = Column(String(500), nullable=True)
    body_html = Column(Text, nullable=False)
    cta_text = Column(String(200), nullable=True)
    cta_url = Column(String(1000), nullable=True)
    target_audience = Column(String(100), default="all")  # all, free, starter, pro, lab, active, inactive
    status = Column(String(50), default="draft")  # draft, scheduled, sending, sent, failed
    ai_generated = Column(Boolean, default=False)
    ai_rationale = Column(Text, nullable=True)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
