"""Migration: add advanced experiment-settings columns.

Adds columns required for ablation studies, multi-algorithm runs, and
per-seed training:

- research_projects.experiment_config_json
- rl_environments.variant_role
- rl_environments.variant_label
- training_runs.seed
- training_runs.variant_role

Idempotent: safe to run repeatedly. Imported by app.main during lifespan startup.
"""
import logging
import os
import sqlite3

logger = logging.getLogger("migrate.advanced_settings")

DEFAULT_DB_PATH = os.environ.get("DB_PATH", "/app/data/bot.db")

# (table, column, sqlite_column_definition)
NEW_COLUMNS = [
    ("research_projects", "experiment_config_json", "TEXT"),
    ("rl_environments",   "variant_role",           "VARCHAR(50)"),
    ("rl_environments",   "variant_label",          "VARCHAR(200)"),
    ("training_runs",     "seed",                   "INTEGER"),
    ("training_runs",     "variant_role",           "VARCHAR(50)"),
]


def _column_exists(cur: sqlite3.Cursor, table: str, column: str) -> bool:
    try:
        cur.execute(f"PRAGMA table_info({table})")
    except sqlite3.OperationalError:
        return False
    return any(row[1] == column for row in cur.fetchall())


def migrate(db_path: str = DEFAULT_DB_PATH) -> None:
    if not os.path.exists(db_path):
        logger.info("DB not found at %s — skipping advanced-settings migration", db_path)
        return

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        for table, col, col_type in NEW_COLUMNS:
            # Skip when the table itself doesn't exist yet — create_all will handle it.
            try:
                cur.execute(f"SELECT 1 FROM {table} LIMIT 1")
            except sqlite3.OperationalError:
                continue
            if _column_exists(cur, table, col):
                continue
            try:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
                logger.info("Added %s.%s", table, col)
            except sqlite3.OperationalError as e:
                logger.warning("Could not add %s.%s: %s", table, col, e)
        conn.commit()
    finally:
        conn.close()


def migrate_from_url(database_url: str) -> None:
    """Best-effort migration that infers the SQLite file path from a SQLAlchemy URL."""
    # Common shapes:
    #   sqlite+aiosqlite:///./bot.db
    #   sqlite+aiosqlite:////app/data/bot.db
    if not database_url:
        return migrate()
    if "sqlite" not in database_url:
        logger.info("Non-sqlite database URL — skipping advanced-settings ALTER migration")
        return
    # strip scheme up to the first '/'.
    path = database_url.split(":///", 1)[-1]
    if path.startswith("/"):
        return migrate(path)
    return migrate(os.path.abspath(path))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    migrate()
