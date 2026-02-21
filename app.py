# app.py

import hmac
import werkzeug.security

# Patch safe_str_cmp for compatibility with older libraries
if not hasattr(werkzeug.security, 'safe_str_cmp'):
    werkzeug.security.safe_str_cmp = hmac.compare_digest

from flask import Flask
from models import db
from routes.auth import auth
from routes.test_routes import test_routes

app = Flask(__name__)

# Load the configuration from config.py
app.config.from_object('config')

# Initialize the database
db.init_app(app)

# Initialize Flask-Login
from flask_login import LoginManager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

from models.user import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Create all tables if they don't already exist
with app.app_context():
    db.create_all()

# Register Blueprints
app.register_blueprint(auth, url_prefix='')  # Accessible via /
app.register_blueprint(test_routes, url_prefix='/test')  # Accessible via /test

if __name__ == '__main__':
    app.run(debug=True)
