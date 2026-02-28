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
    default_ai_model: str = os.getenv("DEFAULT_AI_MODEL", "claude-sonnet-4-20250514")

    # Bot Settings
    tweet_interval_minutes: int = int(os.getenv("TWEET_INTERVAL_MINUTES", "120"))
    auto_reply_enabled: bool = os.getenv("AUTO_REPLY_ENABLED", "true").lower() == "true"

    # Persistent storage — use /app/data on Railway (Volume mount), fallback to local
    data_dir: str = os.getenv("DATA_DIR", "./data" if os.getenv("RAILWAY_ENVIRONMENT") else ".")
    articles_dir: str = os.getenv("ARTICLES_DIR", os.path.join(os.getenv("DATA_DIR", "./data" if os.getenv("RAILWAY_ENVIRONMENT") else "."), "articles"))

    # Database — store in data_dir for persistence
    database_url: str = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{os.path.join(os.getenv('DATA_DIR', './data' if os.getenv('RAILWAY_ENVIRONMENT') else '.'), 'bot.db')}")

    class Config:
        env_file = ".env"


settings = Settings()
