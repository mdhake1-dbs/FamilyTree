"""
Routes package initialization.
Imports all blueprint modules and provides a central registration function.
"""

from .auth_routes import auth_bp
from .people_routes import people_bp
from .relationships_routes import relationships_bp
from .events_routes import events_bp
from .misc_routes import misc_bp

__all__ = [
    'auth_bp',
    'people_bp',
    'relationships_bp',
    'events_bp',
    'misc_bp',
    'register_routes'
]

def register_routes(app):
    """
    Register all blueprints with the Flask app.
    
    Args:
        app: Flask application instance
    """
    # Register API blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(people_bp)
    app.register_blueprint(relationships_bp)
    app.register_blueprint(events_bp)
    
    # Register misc blueprint (includes health check and frontend serving)
    # This should be registered last as it includes catch-all routes
    app.register_blueprint(misc_bp)
