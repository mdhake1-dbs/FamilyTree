__version__ = '1.0.0'
__author__ = 'Mayur'
__all__ = [
    'create_app',
    'Config',
    'get_db_connection',
    'require_auth'
]

from .config import Config
from .database import get_db_connection, init_db, close_db_connection
from .auth_utils import require_auth
from .routes import register_routes


def create_app(config_object=None):

    from flask import Flask
    from flask_cors import CORS

    app = Flask(__name__)
    
    app.config.from_object(config_object or Config)
    CORS(app, supports_credentials=True)

    init_db(app)
    register_routes(app)
    app.teardown_appcontext(close_db_connection)

    return app

