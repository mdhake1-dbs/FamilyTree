import os
import sqlite3
from flask import g, current_app


def init_db(app):

    """
    Ensure DB exists and apply all pending migrations.
    """
    db_path = app.config.get("DB_PATH")
    if not db_path:
        raise RuntimeError("DB_PATH is not configured")

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        _ensure_migration_table(conn)
        _apply_migrations(conn)
    finally:
        conn.close()


def _ensure_migration_table(conn):
    """
    Create schema_migrations table if not exists.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename TEXT PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def _apply_migrations(conn):
    """
    Execute all pending SQL migration files in order.
    """
    migrations_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "db"
        )
    )

    if not os.path.isdir(migrations_dir):
        raise RuntimeError(f"Migration directory not found: {migrations_dir}")

    applied = {
        row[0]
        for row in conn.execute(
            "SELECT filename FROM schema_migrations"
        ).fetchall()
    }


    migration_files = sorted(
        f for f in os.listdir(migrations_dir)
        if f.endswith(".sql")
    )

    for filename in migration_files:
        if filename in applied:
            continue

        filepath = os.path.join(migrations_dir, filename)

        with open(filepath, "r", encoding="utf-8") as f:
            sql = f.read()

        try:
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO schema_migrations (filename) VALUES (?)",
                (filename,)
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise RuntimeError(f"Migration failed: {filename}")


def get_db_connection():
    """
    Return a sqlite3 connection (row factory = sqlite3.Row).
    One connection per request context.
    """
    conn = getattr(g, "_sqlite_conn", None)

    if conn is None:
        conn = sqlite3.connect(
            current_app.config["DB_PATH"],
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row

        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")

        g._sqlite_conn = conn

    return conn


def close_db_connection(exception=None):
    """
    Close database connection on app context teardown.
    """
    conn = getattr(g, "_sqlite_conn", None)
    if conn is not None:
        conn.close()

