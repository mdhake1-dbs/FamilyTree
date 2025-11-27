#!/usr/bin/python3

from flask import Flask, request, jsonify, g
from flask import send_from_directory
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)

# Path to SQLite DB file (container should mount host dir to /app/data)
DB_PATH = os.getenv('SQLITE_DB_PATH', os.path.join(os.getcwd(), 'data', 'demo.db'))

def get_db_connection():
    """Return a sqlite3 connection (row factory = sqlite3.Row)."""
    conn = getattr(g, '_sqlite_conn', None)
    if conn is None:
        # allow multi-threaded access for WSGI servers
        conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # Recommended pragmas for correctness/concurrency
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

# ============= CRUD ENDPOINTS FOR PEOPLE =============

@app.route('/api/people', methods=['GET'])
def get_all_people():
    """Retrieve all people (READ - List)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, given_name, family_name, other_names, gender,
                   birth_date, death_date, birth_place, bio, privacy,
                   created_at, updated_at
            FROM People
            WHERE is_deleted = 0
            ORDER BY family_name, given_name
        """)

        rows = cursor.fetchall()
        people = []
        for row in rows:
            person = dict(row)
            # Ensure date fields are strings (they should already be ISO strings)
            for key in ['birth_date', 'death_date', 'created_at', 'updated_at']:
                if person.get(key) is not None:
                    # leave as-is (assume ISO string); if stored as datetime, convert
                    person[key] = person[key]
            people.append(person)

        return jsonify({'success': True, 'data': people}), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/people/<int:person_id>', methods=['GET'])
def get_person(person_id):
    """Retrieve a single person by ID (READ - Single)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, given_name, family_name, other_names, gender,
                   birth_date, death_date, birth_place, bio, privacy,
                   created_at, updated_at
            FROM People
            WHERE id = ? AND is_deleted = 0
        """, (person_id,))

        row = cursor.fetchone()

        if row:
            person = dict(row)
            for key in ['birth_date', 'death_date', 'created_at', 'updated_at']:
                if person.get(key) is not None:
                    person[key] = person[key]
            return jsonify({'success': True, 'data': person}), 200
        else:
            return jsonify({'success': False, 'error': 'Person not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/people', methods=['POST'])
def create_person():
    """Create a new person (CREATE)"""
    try:
        data = request.get_json() or {}

        # Validate required fields
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
                birth_date, death_date, birth_place, bio, privacy,
                created_at, updated_at, is_deleted
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            data.get('given_name'),
            data.get('family_name'),
            data.get('other_names'),
            data.get('gender'),
            data.get('birth_date'),
            data.get('death_date'),
            data.get('birth_place'),
            data.get('bio'),
            data.get('privacy', 'private'),
            now_iso,
            now_iso
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
def update_person(person_id):
    """Update an existing person (UPDATE)"""
    try:
        data = request.get_json() or {}

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if person exists
        cursor.execute("SELECT id FROM People WHERE id = ? AND is_deleted = 0", (person_id,))
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
                privacy = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            data.get('given_name'),
            data.get('family_name'),
            data.get('other_names'),
            data.get('gender'),
            data.get('birth_date'),
            data.get('death_date'),
            data.get('birth_place'),
            data.get('bio'),
            data.get('privacy'),
            now_iso,
            person_id
        ))

        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Person updated successfully'
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/people/<int:person_id>', methods=['DELETE'])
def delete_person(person_id):
    """Soft delete a person (DELETE)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if person exists
        cursor.execute("SELECT id FROM People WHERE id = ? AND is_deleted = 0", (person_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Person not found'}), 404

        now_iso = datetime.now().isoformat()

        # Soft delete
        cursor.execute("""
            UPDATE People
            SET is_deleted = 1, updated_at = ?
            WHERE id = ?
        """, (now_iso, person_id))

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
        # Simple check: ensure we can open the DB file and run a trivial query
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
    """
    Serve the compiled frontend files (SPA). Place index.html and assets into FRONTEND_DIR.
    """
    FRONTEND_DIR = os.path.join(os.getcwd(), 'frontend')  # adjust if your frontend path differs
    if path != "" and os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    # otherwise return index.html for client-side routing
    return send_from_directory(FRONTEND_DIR, 'index.html')

if __name__ == '__main__':
    # Ensure the containing directory exists (helpful when running locally)
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    app.run(debug=True, host='0.0.0.0', port=80)

