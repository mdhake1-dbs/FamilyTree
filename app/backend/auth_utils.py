import hashlib
import secrets
from datetime import datetime
from functools import wraps
from flask import request, jsonify, g
from database import get_db_connection

def hash_password(password: str) -> str:
    """Simple password hashing (use bcrypt in production)."""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_session_token() -> str:
    """Generate a secure random session token."""
    return secrets.token_urlsafe(32)

def get_current_user():
    """Get current user from session token in Authorization header."""
    token_header = request.headers.get('Authorization')
    if not token_header or not token_header.startswith('Bearer '):
        return None

    token = token_header[7:]  # strip "Bearer "
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT u.id, u.username, u.email, u.full_name
            FROM Sessions s
            JOIN Users u ON s.user_id = u.id
            WHERE s.session_token = ?
              AND s.expires_at > ?
              AND u.is_active = 1
            """,
            (token, datetime.now().isoformat())
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    except Exception:
        return None

def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        g.current_user = user
        return f(*args, **kwargs)
    return decorated
