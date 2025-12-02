#!/usr/bin/python3

from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import hashlib
import secrets
from functools import wraps

load_dotenv()
app = Flask(__name__)
CORS(app, supports_credentials=True)

# Path to SQLite DB file (container should mount host dir to /app/data)
DB_PATH = os.getenv('SQLITE_DB_PATH', os.path.join(os.getcwd(), 'data', 'demo.db'))

# Fixed relationship types used in the Relationships table
RELATION_TYPES = ['father', 'mother', 'brother', 'sister', 'husband', 'wife']


def get_db_connection():
    """Return a sqlite3 connection (row factory = sqlite3.Row)."""
    conn = getattr(g, '_sqlite_conn', None)
    if conn is None:
        conn = sqlite3.connect(
            DB_PATH,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON;')
        conn.execute('PRAGMA journal_mode = WAL;')
        conn.execute('PRAGMA synchronous = NORMAL;')
        g._sqlite_conn = conn
    return conn


@app.teardown_appcontext
def close_db_connection(exception):
    conn = getattr(g, '_sqlite_conn', None)
    if conn is not None:
        conn.close()


# ============= AUTHENTICATION HELPERS =============

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


# ============= AUTH ENDPOINTS =============

@app.route('/api/auth/register', methods=['POST'])
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


@app.route('/api/auth/login', methods=['POST'])
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


@app.route('/api/auth/logout', methods=['POST'])
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


@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user_info():
    """Get current user information."""
    return jsonify({'success': True, 'user': g.current_user}), 200


@app.route('/api/auth/me', methods=['PUT'])
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


# ============= CRUD ENDPOINTS FOR PEOPLE ============= :contentReference[oaicite:1]{index=1}

@app.route('/api/people', methods=['GET'])
@require_auth
def get_all_people():
    """Retrieve all people for current user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, given_name, family_name, other_names, gender,
                   birth_date, death_date, birth_place, bio, relation,
                   created_at, updated_at
            FROM People
            WHERE is_deleted = 0 AND user_id = ?
            ORDER BY family_name, given_name
            """,
            (g.current_user['id'],)
        )
        rows = cursor.fetchall()
        people = [dict(r) for r in rows]
        return jsonify({'success': True, 'data': people}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/people/<int:person_id>', methods=['GET'])
@require_auth
def get_person(person_id):
    """Retrieve a single person by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, given_name, family_name, other_names, gender,
                   birth_date, death_date, birth_place, bio, relation,
                   created_at, updated_at
            FROM People
            WHERE id = ? AND is_deleted = 0 AND user_id = ?
            """,
            (person_id, g.current_user['id'])
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({'success': False, 'error': 'Person not found'}), 404
        return jsonify({'success': True, 'data': dict(row)}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/people', methods=['POST'])
@require_auth
def create_person():
    """Create a new person."""
    try:
        data = request.get_json() or {}
        if not data.get('given_name') or not data.get('family_name'):
            return jsonify({'success': False, 'error': 'Given name and family name are required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        now_iso = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO People (
                given_name, family_name, other_names, gender,
                birth_date, death_date, birth_place, bio, relation,
                created_at, updated_at, is_deleted, user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                data.get('given_name'),
                data.get('family_name'),
                data.get('other_names'),
                data.get('gender'),
                data.get('birth_date'),
                data.get('death_date'),
                data.get('birth_place'),
                data.get('bio'),
                data.get('relation'),
                now_iso,
                now_iso,
                g.current_user['id']
            )
        )
        new_id = cursor.lastrowid
        conn.commit()

        return jsonify({'success': True, 'message': 'Person created successfully', 'id': int(new_id)}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/people/<int:person_id>', methods=['PUT'])
@require_auth
def update_person(person_id):
    """Update an existing person."""
    try:
        data = request.get_json() or {}
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id FROM People
            WHERE id = ? AND is_deleted = 0 AND user_id = ?
            """,
            (person_id, g.current_user['id'])
        )
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Person not found'}), 404

        now_iso = datetime.now().isoformat()

        cursor.execute(
            """
            UPDATE People SET
                given_name = ?,
                family_name = ?,
                other_names = ?,
                gender = ?,
                birth_date = ?,
                death_date = ?,
                birth_place = ?,
                bio = ?,
                relation = ?,
                updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                data.get('given_name'),
                data.get('family_name'),
                data.get('other_names'),
                data.get('gender'),
                data.get('birth_date'),
                data.get('death_date'),
                data.get('birth_place'),
                data.get('bio'),
                data.get('relation'),
                now_iso,
                person_id,
                g.current_user['id']
            )
        )
        conn.commit()
        return jsonify({'success': True, 'message': 'Person updated successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/people/<int:person_id>', methods=['DELETE'])
@require_auth
def delete_person(person_id):
    """Soft delete a person."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id FROM People
            WHERE id = ? AND is_deleted = 0 AND user_id = ?
            """,
            (person_id, g.current_user['id'])
        )
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Person not found'}), 404

        now_iso = datetime.now().isoformat()
        cursor.execute(
            """
            UPDATE People
            SET is_deleted = 1, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (now_iso, person_id, g.current_user['id'])
        )
        conn.commit()

        return jsonify({'success': True, 'message': 'Person deleted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= CRUD ENDPOINTS FOR RELATIONSHIPS =============

@app.route('/api/relationships/types', methods=['GET'])
@require_auth
def get_relationship_types():
    """Return the fixed list of relationship types."""
    return jsonify({'success': True, 'data': RELATION_TYPES}), 200


@app.route('/api/relationships', methods=['GET'])
@require_auth
def get_relationships():
    """Retrieve all relationships for the current user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                r.id,
                r.person1_id,
                p1.given_name || ' ' || p1.family_name AS person1_name,
                r.person2_id,
                p2.given_name || ' ' || p2.family_name AS person2_name,
                r.type,
                r.details,
                r.start_date,
                r.end_date,
                r.created_at,
                r.updated_at
            FROM Relationships r
            JOIN People p1 ON r.person1_id = p1.id
            JOIN People p2 ON r.person2_id = p2.id
            WHERE p1.user_id = ?
              AND p2.user_id = ?
              AND p1.is_deleted = 0
              AND p2.is_deleted = 0
            ORDER BY r.created_at DESC
            """,
            (g.current_user['id'], g.current_user['id'])
        )
        rows = cursor.fetchall()
        rels = [dict(row) for row in rows]
        return jsonify({'success': True, 'data': rels}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/relationships/<int:rel_id>', methods=['GET'])
@require_auth
def get_relationship(rel_id):
    """Retrieve a single relationship by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                r.id,
                r.person1_id,
                p1.given_name || ' ' || p1.family_name AS person1_name,
                r.person2_id,
                p2.given_name || ' ' || p2.family_name AS person2_name,
                r.type,
                r.details,
                r.start_date,
                r.end_date,
                r.created_at,
                r.updated_at
            FROM Relationships r
            JOIN People p1 ON r.person1_id = p1.id
            JOIN People p2 ON r.person2_id = p2.id
            WHERE r.id = ?
              AND p1.user_id = ?
              AND p2.user_id = ?
            """,
            (rel_id, g.current_user['id'], g.current_user['id'])
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({'success': False, 'error': 'Relationship not found'}), 404
        return jsonify({'success': True, 'data': dict(row)}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/relationships', methods=['POST'])
@require_auth
def create_relationship():
    """Create a new relationship between two people."""
    try:
        data = request.get_json() or {}
        person1_id = data.get('person1_id')
        person2_id = data.get('person2_id')
        rel_type = (data.get('type') or '').strip().lower()
        details = data.get('details')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not person1_id or not person2_id:
            return jsonify({'success': False, 'error': 'Both people are required'}), 400
        if person1_id == person2_id:
            return jsonify({'success': False, 'error': 'A person cannot have a relationship with themselves'}), 400
        if rel_type and rel_type not in RELATION_TYPES:
            return jsonify({'success': False, 'error': 'Invalid relationship type'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM People
            WHERE id IN (?, ?)
              AND user_id = ?
              AND is_deleted = 0
            """,
            (person1_id, person2_id, g.current_user['id'])
        )
        row = cursor.fetchone()
        if not row or row['cnt'] != 2:
            return jsonify({'success': False, 'error': 'Both people must exist and belong to the current user'}), 400

        now_iso = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO Relationships (
                person1_id, person2_id, type, details,
                start_date, end_date, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (person1_id, person2_id, rel_type, details, start_date, end_date, now_iso, now_iso)
        )
        new_id = cursor.lastrowid
        conn.commit()

        return jsonify({'success': True, 'message': 'Relationship created successfully', 'id': int(new_id)}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/relationships/<int:rel_id>', methods=['PUT'])
@require_auth
def update_relationship(rel_id):
    """Update an existing relationship."""
    try:
        data = request.get_json() or {}
        person1_id = data.get('person1_id')
        person2_id = data.get('person2_id')
        rel_type = (data.get('type') or '').strip().lower()
        details = data.get('details')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT r.id
            FROM Relationships r
            JOIN People p1 ON r.person1_id = p1.id
            JOIN People p2 ON r.person2_id = p2.id
            WHERE r.id = ?
              AND p1.user_id = ?
              AND p2.user_id = ?
            """,
            (rel_id, g.current_user['id'], g.current_user['id'])
        )
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Relationship not found'}), 404

        if not person1_id or not person2_id:
            return jsonify({'success': False, 'error': 'Both people are required'}), 400
        if person1_id == person2_id:
            return jsonify({'success': False, 'error': 'A person cannot have a relationship with themselves'}), 400
        if rel_type and rel_type not in RELATION_TYPES:
            return jsonify({'success': False, 'error': 'Invalid relationship type'}), 400

        cursor.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM People
            WHERE id IN (?, ?)
              AND user_id = ?
              AND is_deleted = 0
            """,
            (person1_id, person2_id, g.current_user['id'])
        )
        row = cursor.fetchone()
        if not row or row['cnt'] != 2:
            return jsonify({'success': False, 'error': 'Both people must exist and belong to the current user'}), 400

        now_iso = datetime.now().isoformat()
        cursor.execute(
            """
            UPDATE Relationships
            SET person1_id = ?,
                person2_id = ?,
                type       = ?,
                details    = ?,
                start_date = ?,
                end_date   = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (person1_id, person2_id, rel_type, details, start_date, end_date, now_iso, rel_id)
        )
        conn.commit()

        return jsonify({'success': True, 'message': 'Relationship updated successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/relationships/<int:rel_id>', methods=['DELETE'])
@require_auth
def delete_relationship(rel_id):
    """Delete a relationship."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT r.id
            FROM Relationships r
            JOIN People p1 ON r.person1_id = p1.id
            JOIN People p2 ON r.person2_id = p2.id
            WHERE r.id = ?
              AND p1.user_id = ?
              AND p2.user_id = ?
            """,
            (rel_id, g.current_user['id'], g.current_user['id'])
        )
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Relationship not found'}), 404

        cursor.execute("DELETE FROM Relationships WHERE id = ?", (rel_id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Relationship deleted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============= EVENTS ENDPOINTS =============

@app.route('/api/events', methods=['GET'])
@require_auth
def list_events():
    """List all events for the current user"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                e.id,
                e.title,
                e.event_date,
                e.place,
                e.description,
                e.created_by,
                p.given_name || ' ' || p.family_name AS person_name
            FROM Events e
            LEFT JOIN People p ON e.created_by = p.id
            WHERE e.user_id = ?
            ORDER BY
                e.event_date IS NULL,      -- non-null dates first
                e.event_date DESC,
                e.id DESC
        """, (g.current_user['id'],))

        rows = cur.fetchall()
        data = []
        for row in rows:
            data.append({
                'id': row['id'],
                'title': row['title'],
                'event_date': row['event_date'],
                'place': row['place'],
                'description': row['description'],
                'created_by': row['created_by'],
                'person_name': row['person_name']
            })

        return jsonify({'success': True, 'data': data}), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/events', methods=['POST'])
@require_auth
def create_event():
    """Create a new event for a person"""
    try:
        data = request.get_json() or {}

        # Frontend sends `created_by` (person id). We also accept `person_id`.
        person_id = data.get('created_by') or data.get('person_id')
        title = data.get('title', '').strip()
        event_date = data.get('event_date')  # 'YYYY-MM-DD' or None
        place = data.get('place', '')
        description = data.get('description', '')

        if not person_id or not title:
            return jsonify({
                'success': False,
                'error': 'Person and title are required'
            }), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Ensure that person exists and belongs to current user
        cur.execute("""
            SELECT id FROM People
            WHERE id = ? AND user_id = ? AND is_deleted = 0
        """, (person_id, g.current_user['id']))
        person_row = cur.fetchone()
        if not person_row:
            return jsonify({
                'success': False,
                'error': 'Person not found'
            }), 404

        now_iso = datetime.now().isoformat()

        cur.execute("""
            INSERT INTO Events (title, event_date, place, description,
                                created_by, user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, event_date, place, description,
              person_id, g.current_user['id'], now_iso, now_iso))

        event_id = cur.lastrowid
        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Event created successfully',
            'id': event_id
        }), 201

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/events/<int:event_id>', methods=['GET'])
@require_auth
def get_event(event_id):
    """Get a single event by id"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                e.id,
                e.title,
                e.event_date,
                e.place,
                e.description,
                e.created_by,
                p.given_name || ' ' || p.family_name AS person_name
            FROM Events e
            LEFT JOIN People p ON e.created_by = p.id
            WHERE e.id = ? AND e.user_id = ?
        """, (event_id, g.current_user['id']))
        row = cur.fetchone()

        if not row:
            return jsonify({'success': False, 'error': 'Event not found'}), 404

        event = {
            'id': row['id'],
            'title': row['title'],
            'event_date': row['event_date'],
            'place': row['place'],
            'description': row['description'],
            'created_by': row['created_by'],
            'person_name': row['person_name']
        }

        return jsonify({'success': True, 'data': event}), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/events/<int:event_id>', methods=['PUT'])
@require_auth
def update_event(event_id):
    """Update an existing event"""
    try:
        data = request.get_json() or {}

        person_id = data.get('created_by') or data.get('person_id')
        title = data.get('title', '').strip()
        event_date = data.get('event_date')
        place = data.get('place', '')
        description = data.get('description', '')

        if not person_id or not title:
            return jsonify({
                'success': False,
                'error': 'Person and title are required'
            }), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Make sure event exists and belongs to user
        cur.execute("""
            SELECT id FROM Events
            WHERE id = ? AND user_id = ?
        """, (event_id, g.current_user['id']))
        ev_row = cur.fetchone()
        if not ev_row:
            return jsonify({'success': False, 'error': 'Event not found'}), 404

        # Ensure person belongs to user
        cur.execute("""
            SELECT id FROM People
            WHERE id = ? AND user_id = ? AND is_deleted = 0
        """, (person_id, g.current_user['id']))
        person_row = cur.fetchone()
        if not person_row:
            return jsonify({'success': False, 'error': 'Person not found'}), 404

        now_iso = datetime.now().isoformat()

        cur.execute("""
            UPDATE Events
            SET title = ?,
                event_date = ?,
                place = ?,
                description = ?,
                created_by = ?,
                updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (title, event_date, place, description,
              person_id, now_iso, event_id, g.current_user['id']))

        conn.commit()

        return jsonify({'success': True, 'message': 'Event updated successfully'}), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/events/<int:event_id>', methods=['DELETE'])
@require_auth
def delete_event(event_id):
    """Delete an event (hard delete; no is_deleted column on Events)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            DELETE FROM Events
            WHERE id = ? AND user_id = ?
        """, (event_id, g.current_user['id']))

        if cur.rowcount == 0:
            return jsonify({'success': False, 'error': 'Event not found'}), 404

        conn.commit()

        return jsonify({'success': True, 'message': 'Event deleted successfully'}), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



# ============= HEALTH CHECK =============

@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check endpoint."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        cursor.fetchone()
        return jsonify({
            'success': True,
            'message': 'API is running',
            'database': 'connected',
            'db_path': DB_PATH
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'API is running',
            'database': 'disconnected',
            'error': str(e),
            'db_path': DB_PATH
        }), 500


# ============= FRONTEND SPA SERVING =============

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve the compiled frontend files (SPA)."""
    FRONTEND_DIR = os.path.join(os.getcwd(), 'frontend')
    if path != "" and os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, 'index.html')


if __name__ == '__main__':
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    app.run(debug=True, host='0.0.0.0', port=4000)

