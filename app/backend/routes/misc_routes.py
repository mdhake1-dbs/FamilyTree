from flask import Blueprint, jsonify, send_from_directory, current_app
from database import get_db_connection
import os

misc_bp = Blueprint('misc', __name__)

@misc_bp.route('/api/health', methods=['GET'])
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
            'db_path': current_app.config['DB_PATH']
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'API is running',
            'database': 'disconnected',
            'error': str(e),
            'db_path': current_app.config['DB_PATH']
        }), 500

@misc_bp.route('/', defaults={'path': ''})
@misc_bp.route('/<path:path>')
def serve_frontend(path):
    """Serve the compiled frontend files (SPA)."""
    FRONTEND_DIR = os.path.join(os.getcwd(), 'frontend')
    if path != "" and os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, 'index.html')
