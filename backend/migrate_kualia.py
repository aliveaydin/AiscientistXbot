"""Migration script: Add published fields to BlogPost/ResearchPaper + create RLEnvironment table."""
import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "/app/data/bot.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # BlogPost: add published, published_at
    try:
        cur.execute("ALTER TABLE blog_posts ADD COLUMN published BOOLEAN DEFAULT 0")
        print("Added blog_posts.published")
    except sqlite3.OperationalError:
        print("blog_posts.published already exists")

    try:
        cur.execute("ALTER TABLE blog_posts ADD COLUMN published_at DATETIME")
        print("Added blog_posts.published_at")
    except sqlite3.OperationalError:
        print("blog_posts.published_at already exists")

    # ResearchPaper: add published, published_at
    try:
        cur.execute("ALTER TABLE research_papers ADD COLUMN published BOOLEAN DEFAULT 0")
        print("Added research_papers.published")
    except sqlite3.OperationalError:
        print("research_papers.published already exists")

    try:
        cur.execute("ALTER TABLE research_papers ADD COLUMN published_at DATETIME")
        print("Added research_papers.published_at")
    except sqlite3.OperationalError:
        print("research_papers.published_at already exists")

    # RLEnvironment table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rl_environments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(500) NOT NULL,
            description TEXT,
            category VARCHAR(100) DEFAULT 'custom',
            observation_space TEXT,
            action_space TEXT,
            reward_description TEXT,
            code TEXT,
            preview_image TEXT,
            difficulty VARCHAR(50) DEFAULT 'medium',
            status VARCHAR(50) DEFAULT 'draft',
            ai_model_used VARCHAR(50),
            topic TEXT,
            published_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created rl_environments table (if not existed)")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
