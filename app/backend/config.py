import os

class Config:
    """Application configuration"""
    DB_PATH = os.getenv('SQLITE_DB_PATH', os.path.join(os.getcwd(), 'data', 'demo.db'))
    RELATION_TYPES = ['father', 'mother', 'brother', 'sister', 'husband', 'wife']
    SESSION_EXPIRY_DAYS = 7
    MIN_PASSWORD_LENGTH = 6
