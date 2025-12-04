from flask import Blueprint, request, jsonify, g
from datetime import datetime
from ..database import get_db_connection
from ..auth_utils import require_auth

people_bp = Blueprint('people', __name__, url_prefix='/api/people')

@people_bp.route('', methods=['GET'])
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

@people_bp.route('/<int:person_id>', methods=['GET'])
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

@people_bp.route('', methods=['POST'])
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

@people_bp.route('/<int:person_id>', methods=['PUT'])
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

@people_bp.route('/<int:person_id>', methods=['DELETE'])
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
