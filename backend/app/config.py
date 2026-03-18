import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env from project root (parent of backend/)
_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")


class Settings(BaseSettings):
    # Twitter API
    twitter_api_key: str = os.getenv("TWITTER_API_KEY", "")
    twitter_api_secret: str = os.getenv("TWITTER_API_SECRET", "")
    twitter_access_token: str = os.getenv("TWITTER_ACCESS_TOKEN", "")
    twitter_access_token_secret: str = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
    twitter_bearer_token: str = os.getenv("TWITTER_BEARER_TOKEN", "")

    # AI Models
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    default_ai_model: str = os.getenv("DEFAULT_AI_MODEL", "kimi-k2.5")

    # Kimi API (for blog generation)
    kimi_api_key: str = os.getenv("KIMI_API_KEY", "")
    kimi_base_url: str = os.getenv("KIMI_BASE_URL", "https://api.moonshot.ai/v1")
    kimi_model: str = os.getenv("KIMI_MODEL", "kimi-k2.5")

    # Bot Settings
    tweet_interval_minutes: int = int(os.getenv("TWEET_INTERVAL_MINUTES", "120"))
    auto_reply_enabled: bool = os.getenv("AUTO_REPLY_ENABLED", "true").lower() == "true"

    # Cloudflare Worker Proxy (for posting tweets from cloud IPs)
    cf_worker_url: str = os.getenv("CF_WORKER_URL", "")
    cf_worker_secret: str = os.getenv("CF_WORKER_SECRET", "aiscientist-bot-2024")

    # Persistent storage
    data_dir: str = os.getenv("DATA_DIR", "./data")
    articles_dir: str = os.getenv("ARTICLES_DIR", os.path.join(os.getenv("DATA_DIR", "./data"), "articles"))

    # Database
    database_url: str = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{os.path.join(os.getenv('DATA_DIR', './data'), 'bot.db')}")

    class Config:
        env_file = ".env"


settings = Settings()
