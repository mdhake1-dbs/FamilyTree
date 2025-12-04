import sqlite3
from flask import g

def init_db(app):
    """Initialize database configuration"""
    app.config['DB_PATH'] = app.config.get('DB_PATH')

def get_db_connection():
    """Return a sqlite3 connection (row factory = sqlite3.Row)."""
    conn = getattr(g, '_sqlite_conn', None)
    if conn is None:
        from flask import current_app
        conn = sqlite3.connect(
            current_app.config['DB_PATH'],
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON;')
        conn.execute('PRAGMA journal_mode = WAL;')
        conn.execute('PRAGMA synchronous = NORMAL;')
        g._sqlite_conn = conn
    return conn

def close_db_connection(exception):
    """Close database connection on teardown"""
    conn = getattr(g, '_sqlite_conn', None)
    if conn is not None:
        conn.close()
