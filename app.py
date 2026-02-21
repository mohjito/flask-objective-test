# Register Blueprints
app.register_blueprint(auth, url_prefix='')  # Accessible via /
app.register_blueprint(test_routes, url_prefix='/test')  # Accessible via /test

# ============= AUTO-SEEDING FOR RENDER =============
# Ensure instance folder exists
import os
instance_path = os.path.join(os.path.dirname(__file__), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

# Auto-seed database on startup (this WILL run on Render)
with app.app_context():
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'test.db')
    print("=" * 60)
    print(f"🔍 Checking database at: {db_path}")
    print("=" * 60)
    
    # Check if database exists and has data
    if not os.path.exists(db_path):
        print("📦 Database file not found. Creating and seeding...")
        try:
            # Import seed_data here to avoid circular imports
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
# ===================================================

if __name__ == '__main__':
    app.run(debug=True)