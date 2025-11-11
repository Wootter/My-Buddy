import os

class Config:
    # For local development use a SQLite DB file in the project root.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mybuddy.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Secret key for sessions (change this in production!)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
