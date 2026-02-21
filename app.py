import hmac
import os
import sys
import traceback
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

# Detect if running on Render
if os.environ.get('RENDER'):
    print("=" * 60)
    print("🚀 Running on Render - using /tmp for database")
    print("=" * 60)

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

# ===== HEALTH CHECK ENDPOINT FOR UPTIME MONITORS =====
@app.route('/ping')
def ping():
    """Simple endpoint for uptime monitors to keep the app alive"""
    return "OK", 200

# ===== DEBUG ROUTE TO CHECK DATABASE STATUS =====
@app.route('/debug')
def debug_info():
    import os
    result = "<h2>🔍 Debug Information</h2>"
    
    # Check database path
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    result += f"<p><b>Database path:</b> {db_path}</p>"
    result += f"<p><b>Database exists:</b> {os.path.exists(db_path)}</p>"
    
    # Check data folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data')
    result += f"<p><b>Data folder:</b> {data_dir}</p>"
    result += f"<p><b>Data folder exists:</b> {os.path.exists(data_dir)}</p>"
    
    if os.path.exists(data_dir):
        json_files = []
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(os.path.relpath(os.path.join(root, file), script_dir))
        result += f"<p><b>JSON files found:</b> {len(json_files)}</p>"
        if json_files:
            result += "<ul>"
            for f in json_files[:10]:  # Show first 10
                result += f"<li>{f}</li>"
            if len(json_files) > 10:
                result += f"<li>... and {len(json_files)-10} more</li>"
            result += "</ul>"
    
    # Check database content
    try:
        from models.test import Test
        test_count = Test.query.count()
        result += f"<p><b>Tests in database:</b> {test_count}</p>"
        
        if test_count > 0:
            tests = Test.query.limit(5).all()
            result += "<h3>Sample Tests:</h3><ul>"
            for test in tests:
                result += f"<li>{test.name} ({test.category} - {test.year}) - {len(test.questions)} questions</li>"
            result += "</ul>"
    except Exception as e:
        result += f"<p><b>Error querying tests:</b> {str(e)}</p>"
    
    # Check users
    try:
        from models.user import User
        user_count = User.query.count()
        result += f"<p><b>Users in database:</b> {user_count}</p>"
    except:
        result += f"<p><b>Users:</b> Not available</p>"
    
    return result

# ===== MANUAL SEED ROUTE =====
@app.route('/force-seed')
def force_seed():
    try:
        from seed_data import seed_data, seed_users
        with app.app_context():
            seed_data()
            seed_users()
            return "✅ Database seeded successfully! <a href='/'>Go to Home</a>"
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"❌ Error: {str(e)}"

# Create all tables if they don't already exist
with app.app_context():
    db.create_all()
    print("✅ Database tables created/verified")

# Ensure necessary directories exist
with app.app_context():
    # Get database path from config
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    db_dir = os.path.dirname(db_path)
    
    # Create directory if it doesn't exist
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"📁 Created directory: {db_dir}")

# Auto-seed database on startup (for Render)
with app.app_context():
    # Get database path from config
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    print("=" * 60)
    print(f"🔍 Checking database at: {db_path}")
    print("=" * 60)
    
    # Check if database exists and has data
    if not os.path.exists(db_path):
        print("📦 Database file not found. Creating and seeding...")
        try:
            from seed_data import seed_data, seed_users
            seed_data()
            seed_users()
            print("✅ Database created and seeded successfully!")
        except Exception as e:
            print(f"❌ Error seeding database: {e}")
            traceback.print_exc()
    else:
        print("📦 Database file exists. Checking content...")
        try:
            from models.test import Test
            test_count = Test.query.count()
            print(f"📊 Found {test_count} tests in database")
            
            if test_count == 0:
                print("⚠️ Database exists but empty. Seeding...")
                from seed_data import seed_data, seed_users
                seed_data()
                seed_users()
            else:
                print("✅ Database already has test data, no seeding needed")
                
            # Check for users
            try:
                from models.user import User
                user_count = User.query.count()
                print(f"👤 Found {user_count} users in database")
            except:
                print("👤 User table exists but no users or not accessible")
                
        except Exception as e:
            print(f"⚠️ Error checking database: {e}")
            print("Attempting to seed anyway...")
            try:
                from seed_data import seed_data, seed_users
                seed_data()
                seed_users()
            except Exception as e2:
                print(f"❌ Error seeding database: {e2}")
                traceback.print_exc()

if __name__ == '__main__':
    app.run(debug=True)