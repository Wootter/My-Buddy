import os

class Config:
    # For local development use a SQLite DB file in the project root.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mybuddy.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Secret key for sessions - loaded from environment variable
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-only-for-local-testing')
