#!/usr/bin/python3

from flask import Flask, request, jsonify, g
from flask import send_from_directory
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

def get_db_connection():
    """Return a sqlite3 connection (row factory = sqlite3.Row)."""
    conn = getattr(g, '_sqlite_conn', None)
    if conn is None:
        conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, check_same_thread=False)
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

def hash_password(password):
    """Simple password hashing (use bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_session_token():
    """Generate a secure random session token"""
    return secrets.token_urlsafe(32)

def get_current_user():
    """Get current user from session token"""
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        return None
    
    token = token[7:]  # Remove 'Bearer ' prefix
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.id, u.username, u.email, u.full_name
            FROM Sessions s
            JOIN Users u ON s.user_id = u.id
            WHERE s.session_token = ? 
            AND s.expires_at > ?
            AND u.is_active = 1
        """, (token, datetime.now().isoformat()))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    except Exception:
        return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function

# ============= AUTH ENDPOINTS =============

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json() or {}
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        full_name = data.get('full_name', '').strip()
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Username and password are required'
            }), 400
        
        if len(password) < 6:
            return jsonify({
                'success': False,
                'error': 'Password must be at least 6 characters'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username exists
        cursor.execute("SELECT id FROM Users WHERE username = ?", (username,))
        if cursor.fetchone():
            return jsonify({
                'success': False,
                'error': 'Username already exists'
            }), 400
        
        now_iso = datetime.now().isoformat()
        password_hash = hash_password(password)
        
        cursor.execute("""
            INSERT INTO Users (username, password_hash, email, full_name, created_at, updated_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (username, password_hash, email, full_name, now_iso, now_iso))
        
        user_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user_id': int(user_id)
        }), 201
        
    except sqlite3.IntegrityError as e:
        return jsonify({
            'success': False,
            'error': 'Username or email already exists'
        }), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user and create session"""
    try:
        data = request.get_json() or {}
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Username and password are required'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        
        cursor.execute("""
            SELECT id, username, email, full_name
            FROM Users
            WHERE username = ? AND password_hash = ? AND is_active = 1
        """, (username, password_hash))
        
        user_row = cursor.fetchone()
        
        if not user_row:
            return jsonify({
                'success': False,
                'error': 'Invalid username or password'
            }), 401
        
        user = dict(user_row)
        
        # Create session
        session_token = generate_session_token()
        now = datetime.now()
        expires_at = now + timedelta(days=7)  # Session valid for 7 days
        
        cursor.execute("""
            INSERT INTO Sessions (user_id, session_token, created_at, expires_at)
            VALUES (?, ?, ?, ?)
        """, (user['id'], session_token, now.isoformat(), expires_at.isoformat()))
        
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
    """Logout user and invalidate session"""
    try:
        token = request.headers.get('Authorization', '')[7:]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM Sessions WHERE session_token = ?", (token,))
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user_info():
    """Get current user information"""
    return jsonify({
        'success': True,
        'user': g.current_user
    }), 200

@app.route('/api/auth/me', methods=['PUT'])
@require_auth
def update_current_user():
    """Update current user's email / full_name / password"""
    try:
        data = request.get_json() or {}
        email = data.get('email')
        full_name = data.get('full_name')
        new_password = data.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build update dynamically
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

        # Return new user info
        cursor.execute("SELECT id, username, email, full_name FROM Users WHERE id = ?", (g.current_user['id'],))
        user_row = cursor.fetchone()
        user = dict(user_row) if user_row else None

        return jsonify({'success': True, 'user': user}), 200

    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Email already in use'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============= CRUD ENDPOINTS FOR PEOPLE (with auth) =============
# Note: relation column is added/used here (frontend will send/receive relation)

@app.route('/api/people', methods=['GET'])
@require_auth
def get_all_people():
    """Retrieve all people for current user (READ - List)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, given_name, family_name, other_names, gender,
                   birth_date, death_date, birth_place, bio, relation,
                   created_at, updated_at
            FROM People
            WHERE is_deleted = 0 AND user_id = ?
            ORDER BY family_name, given_name
        """, (g.current_user['id'],))

        rows = cursor.fetchall()
        people = [dict(row) for row in rows]

        return jsonify({'success': True, 'data': people}), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/people/<int:person_id>', methods=['GET'])
@require_auth
def get_person(person_id):
    """Retrieve a single person by ID (READ - Single)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, given_name, family_name, other_names, gender,
                   birth_date, death_date, birth_place, bio, relation,
                   created_at, updated_at
            FROM People
            WHERE id = ? AND is_deleted = 0 AND user_id = ?
        """, (person_id, g.current_user['id']))

        row = cursor.fetchone()

        if row:
            person = dict(row)
            return jsonify({'success': True, 'data': person}), 200
        else:
            return jsonify({'success': False, 'error': 'Person not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/people', methods=['POST'])
@require_auth
def create_person():
    """Create a new person (CREATE)"""
    try:
        data = request.get_json() or {}

        if not data.get('given_name') or not data.get('family_name'):
            return jsonify({
                'success': False,
                'error': 'Given name and family name are required'
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        now_iso = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO People (
                given_name, family_name, other_names, gender,
                birth_date, death_date, birth_place, bio, relation,
                created_at, updated_at, is_deleted, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
        """, (
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
        ))

        new_id = cursor.lastrowid
        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Person created successfully',
            'id': int(new_id)
        }), 201

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/people/<int:person_id>', methods=['PUT'])
@require_auth
def update_person(person_id):
    """Update an existing person (UPDATE)"""
    try:
        data = request.get_json() or {}

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if person exists and belongs to user
        cursor.execute("""
            SELECT id FROM People 
            WHERE id = ? AND is_deleted = 0 AND user_id = ?
        """, (person_id, g.current_user['id']))
        
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Person not found'}), 404

        now_iso = datetime.now().isoformat()

        cursor.execute("""
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
        """, (
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
        ))

        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Person updated successfully'
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/people/<int:person_id>', methods=['DELETE'])
@require_auth
def delete_person(person_id):
    """Soft delete a person (DELETE)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if person exists and belongs to user
        cursor.execute("""
            SELECT id FROM People 
            WHERE id = ? AND is_deleted = 0 AND user_id = ?
        """, (person_id, g.current_user['id']))
        
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Person not found'}), 404

        now_iso = datetime.now().isoformat()

        cursor.execute("""
            UPDATE People
            SET is_deleted = 1, updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (now_iso, person_id, g.current_user['id']))

        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Person deleted successfully'
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============= HEALTH CHECK =============

@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
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
        
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve the compiled frontend files (SPA)"""
    FRONTEND_DIR = os.path.join(os.getcwd(), 'frontend')
    if path != "" and os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, 'index.html')

if __name__ == '__main__':
    
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    app.run(debug=True, host='0.0.0.0', port=80)

