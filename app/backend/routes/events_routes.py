from flask import Blueprint, request, jsonify, g
from datetime import datetime
from ..database import get_db_connection
from ..auth_utils import require_auth

events_bp = Blueprint('events', __name__, url_prefix='/api/events')

@events_bp.route('', methods=['GET'])
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
                e.event_date IS NULL,
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

@events_bp.route('', methods=['POST'])
@require_auth
def create_event():
    """Create a new event for a person"""
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

@events_bp.route('/<int:event_id>', methods=['GET'])
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

@events_bp.route('/<int:event_id>', methods=['PUT'])
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

        cur.execute("""
            SELECT id FROM Events
            WHERE id = ? AND user_id = ?
        """, (event_id, g.current_user['id']))
        ev_row = cur.fetchone()
        if not ev_row:
            return jsonify({'success': False, 'error': 'Event not found'}), 404

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

@events_bp.route('/<int:event_id>', methods=['DELETE'])
@require_auth
def delete_event(event_id):
    """Delete an event (hard delete)"""
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
