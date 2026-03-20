"""
Migration script to add auth-related tables and columns.
Run once: python migrate_auth.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.getenv("DATA_DIR", "."), "bot.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clerk_id VARCHAR(200) UNIQUE NOT NULL,
            email VARCHAR(500),
            username VARCHAR(200) UNIQUE,
            display_name VARCHAR(500),
            avatar_url TEXT,
            bio TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_clerk_id ON users(clerk_id)")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users(username)")
    print("[OK] users table created")

    # 2. Add user_id to rl_environments
    try:
        cursor.execute("ALTER TABLE rl_environments ADD COLUMN user_id INTEGER REFERENCES users(id)")
        print("[OK] rl_environments.user_id added")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[SKIP] rl_environments.user_id already exists")
        else:
            raise

    # 3. Add research_project_id to rl_environments
    try:
        cursor.execute("ALTER TABLE rl_environments ADD COLUMN research_project_id INTEGER REFERENCES research_projects(id)")
        print("[OK] rl_environments.research_project_id added")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[SKIP] rl_environments.research_project_id already exists")
        else:
            raise

    # 4. Add user_id to research_projects
    try:
        cursor.execute("ALTER TABLE research_projects ADD COLUMN user_id INTEGER REFERENCES users(id)")
        print("[OK] research_projects.user_id added")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[SKIP] research_projects.user_id already exists")
        else:
            raise

    # 5. Add phase_running to research_projects
    try:
        cursor.execute("ALTER TABLE research_projects ADD COLUMN phase_running BOOLEAN DEFAULT 0")
        print("[OK] research_projects.phase_running added")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[SKIP] research_projects.phase_running already exists")
        else:
            raise

    conn.commit()
    conn.close()
    print("\n[DONE] Auth migration complete!")


if __name__ == "__main__":
    migrate()
