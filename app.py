import hmac
import os
import sys
import werkzeug.security

# Patch safe_str_cmp for compatibility with older libraries
if not hasattr(werkzeug.security, 'safe_str_cmp'):
    werkzeug.security.safe_str_cmp = hmac.compare_digest

from flask import Flask
from models import db
from routes.auth import auth
from routes.test_routes import test_routes

# ===== CREATE APP FIRST =====
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

# ===== REGISTER BLUEPRINTS AFTER APP IS CREATED =====
app.register_blueprint(auth, url_prefix='')  # Accessible via /
app.register_blueprint(test_routes, url_prefix='/test')  # Accessible via /test

# Create all tables if they don't already exist
with app.app_context():
    db.create_all()

# Ensure instance folder exists
instance_path = os.path.join(os.path.dirname(__file__), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

# Auto-seed database on startup (for Render)
with app.app_context():
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'test.db')
    print("=" * 60)
    print(f"🔍 Checking database at: {db_path}")
    print("=" * 60)
    
    # Check if database exists and has data
    if not os.path.exists(db_path):
        print("📦 Database file not found. Creating and seeding...")
        try:
            from seed_data import seed_data
            seed_data()
            print("✅ Database created and seeded successfully!")
        except Exception as e:
            print(f"❌ Error seeding database: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("📦 Database file exists. Checking content...")
        try:
            from models.test import Test
            test_count = Test.query.count()
            print(f"📊 Found {test_count} tests in database")
            
            if test_count == 0:
                print("⚠️ Database exists but empty. Seeding...")
                from seed_data import seed_data
                seed_data()
            else:
                print("✅ Database already has data, no seeding needed")
        except Exception as e:
            print(f"⚠️ Error checking database: {e}")
            print("Attempting to seed anyway...")
            try:
                from seed_data import seed_data
                seed_data()
            except Exception as e2:
                print(f"❌ Error seeding database: {e2}")
                import traceback
                traceback.print_exc()

if __name__ == '__main__':
    app.run(debug=True)