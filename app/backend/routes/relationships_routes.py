from flask import Blueprint, request, jsonify, g, current_app
from datetime import datetime
from database import get_db_connection
from auth_utils import require_auth

relationships_bp = Blueprint('relationships', __name__, url_prefix='/api/relationships')

@relationships_bp.route('/types', methods=['GET'])
@require_auth
def get_relationship_types():
    """Return the fixed list of relationship types."""
    return jsonify({'success': True, 'data': current_app.config['RELATION_TYPES']}), 200

@relationships_bp.route('', methods=['GET'])
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

@relationships_bp.route('/<int:rel_id>', methods=['GET'])
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

@relationships_bp.route('', methods=['POST'])
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
        if rel_type and rel_type not in current_app.config['RELATION_TYPES']:
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

@relationships_bp.route('/<int:rel_id>', methods=['PUT'])
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
        if rel_type and rel_type not in current_app.config['RELATION_TYPES']:
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

@relationships_bp.route('/<int:rel_id>', methods=['DELETE'])
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
