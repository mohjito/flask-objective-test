import os

# Get the base directory
basedir = os.path.abspath(os.path.dirname(__file__))

# Secret key - use environment variable in production
SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_here'

# For Render, use /tmp directory which is writable
if os.environ.get('RENDER'):
    # On Render, use /tmp for database
    db_path = '/tmp/test.db'
    print(f"📁 Render detected, using database at: {db_path}")
else:
    # Local development - use instance folder
    db_path = os.path.join(basedir, 'instance', 'test.db')
    # Ensure instance folder exists locally
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
SQLALCHEMY_TRACK_MODIFICATIONS = False