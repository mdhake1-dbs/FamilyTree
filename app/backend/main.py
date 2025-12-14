#!/usr/bin/python3

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

from app.backend.config import Config
from app.backend.database import init_db, close_db_connection
from app.backend.routes import register_routes

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, supports_credentials=True)

# Initialize database
init_db(app)

# Register all routes
register_routes(app)

# Teardown database connection
app.teardown_appcontext(close_db_connection)

if __name__ == '__main__':
    # Ensure database directory exists
    db_dir = os.path.dirname(app.config['DB_PATH'])
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    app.run(debug=True, host='0.0.0.0', port=4000)
