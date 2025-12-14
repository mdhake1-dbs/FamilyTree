import os

#Make Sure to have Base Directory configured to Project Root [app/]
BASE_DIR = os.path.abspath(

    os.path.join(os.path.dirname(__file__), "..") 
)

class Config:
    """Application configuration"""

    DB_PATH = os.getenv(
        "SQLITE_DB_PATH",
        os.path.join(BASE_DIR, "data", "familytree.db")
    )

    RELATION_TYPES = [
        'father', 'mother', 'brother',
        'sister', 'husband', 'wife'
    ]

    SESSION_EXPIRY_DAYS = 7
    MIN_PASSWORD_LENGTH = 6

