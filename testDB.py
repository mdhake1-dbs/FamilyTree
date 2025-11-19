import pyodbc
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

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
            return person
        else:
            conn.close()
            return "Failed"
            
    except Exception as e:
        return "Failed"
        
def main():

    print("Hello World!")
    print(get_person(77))
    print("Hello World!")

if __name__ == "__main__":
    main()


