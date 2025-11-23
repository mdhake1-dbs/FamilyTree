from flask import Flask, request, jsonify
from flask_cors import CORS
import pyodbc
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Database configuration
DB_CONFIG = {
    'server': os.getenv('DB_SERVER', 'localhost'),
    'database': os.getenv('DB_NAME', 'demoDB'),
    'username': os.getenv('DB_USER', 'test'),
    'password': os.getenv('DB_PASSWORD', 'test@123'),
    'driver': '{ODBC Driver 17 for SQL Server}'
}

def get_db_connection():
    """Create and return database connection"""
    conn_str = (
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']}"
    )
    return pyodbc.connect(conn_str)

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
        
        columns = [column[0] for column in cursor.description]
        people = []
        
        for row in cursor.fetchall():
            person = dict(zip(columns, row))
            # Convert datetime objects to strings
            for key in ['birth_date', 'death_date', 'created_at', 'updated_at']:
                if person[key]:
                    person[key] = person[key].isoformat()
            people.append(person)
        
        conn.close()
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
        """, person_id)
        
        row = cursor.fetchone()
        
        if row:
            columns = [column[0] for column in cursor.description]
            person = dict(zip(columns, row))
            # Convert datetime objects to strings
            for key in ['birth_date', 'death_date', 'created_at', 'updated_at']:
                if person[key]:
                    person[key] = person[key].isoformat()
            conn.close()
            return jsonify({'success': True, 'data': person}), 200
        else:
            conn.close()
            return jsonify({'success': False, 'error': 'Person not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/people', methods=['POST'])
def create_person():
    """Create a new person (CREATE)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('given_name') or not data.get('family_name'):
            return jsonify({
                'success': False, 
                'error': 'Given name and family name are required'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO People (
                given_name, family_name, other_names, gender,
                birth_date, death_date, birth_place, bio, privacy,
                created_at, updated_at, is_deleted
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0);
            SELECT SCOPE_IDENTITY();
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
            datetime.now(),
            datetime.now()
        ))
        
        new_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
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
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if person exists
        cursor.execute("SELECT id FROM People WHERE id = ? AND is_deleted = 0", person_id)
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Person not found'}), 404
        
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
            datetime.now(),
            person_id
        ))
        
        conn.commit()
        conn.close()
        
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
        cursor.execute("SELECT id FROM People WHERE id = ? AND is_deleted = 0", person_id)
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Person not found'}), 404
        
        # Soft delete
        cursor.execute("""
            UPDATE People 
            SET is_deleted = 1, updated_at = ?
            WHERE id = ?
        """, (datetime.now(), person_id))
        
        conn.commit()
        conn.close()
        
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
        conn.close()
        return jsonify({
            'success': True, 
            'message': 'API is running',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': 'API is running',
            'database': 'disconnected',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
