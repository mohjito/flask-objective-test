import os

# Get the base directory
basedir = os.path.abspath(os.path.dirname(__file__))

# Secret key - use environment variable in production
SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_here'

# Database - use environment variable in production or fallback to SQLite
# Store in instance folder to avoid permission issues
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    'sqlite:///' + os.path.join(basedir, 'instance', 'test.db')

SQLALCHEMY_TRACK_MODIFICATIONS = False