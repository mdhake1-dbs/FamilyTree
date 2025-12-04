from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
import sqlite3
from ..database import get_db_connection
from ..auth_utils import hash_password, generate_session_token, require_auth

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = (data.get('email') or '').strip()
        full_name = (data.get('full_name') or '').strip()

        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password are required'}), 400

        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM Users WHERE username = ?", (username,))
        if cursor.fetchone():
            return jsonify({'success': False, 'error': 'Username already exists'}), 400

        now_iso = datetime.now().isoformat()
        password_hash = hash_password(password)

        cursor.execute(
            """
            INSERT INTO Users (username, password_hash, email, full_name, created_at, updated_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            (username, password_hash, email, full_name, now_iso, now_iso)
        )

        user_id = cursor.lastrowid
        conn.commit()

        return jsonify({'success': True, 'message': 'User registered successfully', 'user_id': int(user_id)}), 201

    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Username or email already exists'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and create a session."""
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password are required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        password_hash = hash_password(password)

        cursor.execute(
            """
            SELECT id, username, email, full_name
            FROM Users
            WHERE username = ? AND password_hash = ? AND is_active = 1
            """,
            (username, password_hash)
        )
        user_row = cursor.fetchone()
        if not user_row:
            return jsonify({'success': False, 'error': 'Invalid username or password'}), 401

        user = dict(user_row)
        session_token = generate_session_token()
        now = datetime.now()
        expires_at = now + timedelta(days=7)

        cursor.execute(
            """
            INSERT INTO Sessions (user_id, session_token, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (user['id'], session_token, now.isoformat(), expires_at.isoformat())
        )
        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': session_token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name']
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Logout user and invalidate session."""
    try:
        token_header = request.headers.get('Authorization', '')
        token = token_header[7:] if token_header.startswith('Bearer ') else None

        if token:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Sessions WHERE session_token = ?", (token,))
            conn.commit()

        return jsonify({'success': True, 'message': 'Logout successful'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user_info():
    """Get current user information."""
    return jsonify({'success': True, 'user': g.current_user}), 200

@auth_bp.route('/me', methods=['PUT'])
@require_auth
def update_current_user():
    """Update current user's profile and password."""
    try:
        data = request.get_json() or {}
        email = data.get('email')
        full_name = data.get('full_name')
        new_password = data.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()

        updates = []
        params = []

        if email is not None:
            updates.append("email = ?")
            params.append(email.strip())

        if full_name is not None:
            updates.append("full_name = ?")
            params.append(full_name.strip())

        if new_password:
            if len(new_password) < 6:
                return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
            updates.append("password_hash = ?")
            params.append(hash_password(new_password))

        if not updates:
            return jsonify({'success': False, 'error': 'No fields provided to update'}), 400

        params.append(datetime.now().isoformat())
        params.append(g.current_user['id'])

        sql = f"UPDATE Users SET {', '.join(updates)}, updated_at = ? WHERE id = ?"
        cursor.execute(sql, tuple(params))
        conn.commit()

        cursor.execute("SELECT id, username, email, full_name FROM Users WHERE id = ?", (g.current_user['id'],))
        user_row = cursor.fetchone()
        user = dict(user_row) if user_row else None

        return jsonify({'success': True, 'user': user}), 200

    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Email already in use'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
