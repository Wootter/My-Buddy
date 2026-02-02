import os

class Config:
    # For local development use a SQLite DB file in the project root.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mybuddy.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Secret key for sessions - loaded from environment variable
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-only-for-local-testing')
    
    # Security settings - CRITICAL for protecting user credentials
    SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript from accessing session cookies
    SESSION_COOKIE_SAMESITE = 'Lax'  # Prevent CSRF attacks
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
