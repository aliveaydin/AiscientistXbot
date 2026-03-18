"""Migration script: Add RLForge columns and tables."""
import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "/app/data/bot.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ── RLEnvironment: new columns ──
    new_cols = [
        ("rl_environments", "slug", "VARCHAR(200) UNIQUE"),
        ("rl_environments", "env_spec_json", "TEXT"),
        ("rl_environments", "test_results_json", "TEXT"),
        ("rl_environments", "version", "INTEGER DEFAULT 1"),
        ("rl_environments", "generation_log", "TEXT"),
        ("rl_environments", "is_template", "BOOLEAN DEFAULT 0"),
        ("rl_environments", "domain", "VARCHAR(100)"),
        ("rl_environments", "max_steps", "INTEGER DEFAULT 1000"),
        ("rl_environments", "api_enabled", "BOOLEAN DEFAULT 1"),
    ]
    for table, col, col_type in new_cols:
        try:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            print(f"Added {table}.{col}")
        except sqlite3.OperationalError:
            print(f"{table}.{col} already exists")

    # ── BuilderConversation ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS builder_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            env_id INTEGER NOT NULL REFERENCES rl_environments(id),
            role VARCHAR(50) NOT NULL,
            content TEXT NOT NULL,
            version_snapshot INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created builder_conversations table (if not existed)")

    # ── TrainingRun ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS training_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            env_id INTEGER NOT NULL REFERENCES rl_environments(id),
            algorithm VARCHAR(50) NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            config_json TEXT,
            results_json TEXT,
            model_path VARCHAR(500),
            training_curve_json TEXT,
            started_at DATETIME,
            completed_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created training_runs table (if not existed)")

    # ── EnvVersion ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS env_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            env_id INTEGER NOT NULL REFERENCES rl_environments(id),
            version INTEGER NOT NULL,
            code TEXT,
            spec_json TEXT,
            change_summary TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created env_versions table (if not existed)")

    # ── SkillCache ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS skill_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_key VARCHAR(200) UNIQUE NOT NULL,
            skill_prompt TEXT NOT NULL,
            usage_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created skill_cache table (if not existed)")

    conn.commit()
    conn.close()
    print("RLForge migration complete.")


if __name__ == "__main__":
    migrate()
