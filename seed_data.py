print("=" * 60)
print("📚 SEED_DATA.PY IS BEING LOADED!")
print("=" * 60)

import json
import os
import sys
from app import app
from models import db
from models.test import Test, Question
from models.result import TestResult

print(f"📁 Python path: {sys.path}")

def seed_data():
    """Main function to seed the database with all JSON files"""
    
    with app.app_context():
        print("🚀 Starting database seeding process...")
        print("=" * 50)
        
        # Get database path for logging
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        print(f"📁 Using database at: {db_path}")
        
        # Create tables if they don't exist
        print("🔄 Ensuring database schema exists...")
        db.create_all()
        print("✅ Database schema ready!")
        
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct path to data folder relative to script
        data_dir = os.path.join(script_dir, 'data')
        
        print(f"📁 Looking for data in: {data_dir}")
        print(f"📁 Data directory exists: {os.path.exists(data_dir)}")
        
        if not os.path.exists(data_dir):
            print(f"❌ Data directory not found: {data_dir}")
            print("Creating data directory...")
            os.makedirs(data_dir, exist_ok=True)
            print(f"✅ Created {data_dir}")
            print("Please add your JSON files to this directory and redeploy.")
            return
        
        # Statistics
        stats = {
            'total_tests': 0,
            'total_questions': 0,
            'categories': set(),
            'years': set(),
            'sections': set(),
            'files_processed': 0,
            'files_failed': 0
        }
        
        # Walk through all subdirectories and process JSON files
        print("\n📂 Scanning for JSON files...")
        
        json_files_found = False
        all_files = []
        
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.endswith('.json'):
                    json_files_found = True
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)
        
        print(f"📊 Found {len(all_files)} JSON files total")
        
        for file_path in all_files:
            relative_path = os.path.relpath(file_path, data_dir)
            print(f"\n📄 Processing: {relative_path}")
            
            success = process_json_file(file_path, stats)
            
            if success:
                stats['files_processed'] += 1
                # Commit after each successful file to save progress
                try:
                    db.session.commit()
                    print(f"  ✅ Committed {relative_path}")
                except Exception as e:
                    print(f"  ❌ Error committing: {e}")
                    db.session.rollback()
            else:
                stats['files_failed'] += 1
        
        if not json_files_found:
            print(f"\n❌ No JSON files found in {data_dir}")
            return
        
        # Final commit for any remaining changes
        try:
            db.session.commit()
            print(f"\n✅ Successfully committed all changes to database!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error in final commit: {e}")
            return
        
        # Print summary
        print_summary(stats)
        
        # Verify the data
        verify_database()

def process_json_file(file_path, stats):
    """Process a single JSON file and add to database"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            root_data = json.load(f)
        
        # Validate required fields
        required_fields = ['name', 'category', 'year', 'section', 'duration', 'questions']
        
        # Collect all potential test objects
        test_objects = []
        
        # Check if the root itself is a test object (Flat structure)
        if all(field in root_data for field in required_fields):
            test_objects.append(root_data)
        else:
            # Check for nested test objects (e.g., {"part1": {...}, "part2": {...}})
            for key, value in root_data.items():
                if isinstance(value, dict) and all(field in value for field in required_fields):
                    test_objects.append(value)
        
        if not test_objects:
            # For logging purposes, find out what's missing in the first dict found
            missing = []
            if isinstance(root_data, dict):
                missing = [f for f in required_fields if f not in root_data]
            
            print(f"  ⚠️  Skipping: {os.path.basename(file_path)} - No valid test data found (missing fields: {missing})")
            return False
        
        any_success = False
        
        for paper_data in test_objects:
            # Check if test already exists
            existing_test = Test.query.filter_by(
                name=paper_data['name'],
                category=paper_data['category'],
                year=paper_data['year'],
                section=paper_data['section']
            ).first()
            
            if existing_test:
                print(f"  ⏭️  Test already exists, skipping: {paper_data['name']}")
                any_success = True  # Count as success if it already exists
                continue
            
            # Create test
            test = Test(
                name=paper_data['name'],
                category=paper_data['category'],
                year=paper_data['year'],
                section=paper_data['section'],
                duration=paper_data['duration']
            )
            
            db.session.add(test)
            db.session.flush()  # Get test ID without committing
            
            # Update stats
            stats['total_tests'] += 1
            stats['categories'].add(paper_data['category'])
            stats['years'].add(paper_data['year'])
            stats['sections'].add(paper_data['section'])
            
            # Add questions
            questions_added = 0
            for q_data in paper_data['questions']:
                # Validate question fields
                if not all(k in q_data for k in ['question', 'options', 'answer']):
                    print(f"    ⚠️  Skipping question missing required fields")
                    continue
                
                question = Question(
                    serial_no=q_data.get('serial_no'),
                    question=q_data['question'],
                    question_hindi=q_data.get('question_hindi', q_data['question']),
                    passage=q_data.get('passage'),
                    passage_hindi=q_data.get('passage_hindi', q_data.get('passage')),
                    options=q_data['options'],
                    options_hindi=q_data.get('options_hindi', q_data['options']),
                    correct_answer=q_data['answer'],
                    test_id=test.id
                )
                
                db.session.add(question)
                questions_added += 1
            
            stats['total_questions'] += questions_added
            print(f"  ✅ Loaded: {paper_data['name']} ({questions_added} questions)")
            any_success = True
        
        return any_success
        
    except json.JSONDecodeError as e:
        print(f"  ❌ Error parsing JSON in {os.path.basename(file_path)}: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error processing file {os.path.basename(file_path)}: {e}")
        import traceback
        traceback.print_exc()
        return False

def print_summary(stats):
    """Print summary of seeding operation"""
    
    print("\n" + "=" * 50)
    print("📊 SEEDING SUMMARY")
    print("=" * 50)
    print(f"📁 Files processed: {stats['files_processed']}")
    print(f"❌ Files failed: {stats['files_failed']}")
    print(f"📝 Total tests created: {stats['total_tests']}")
    print(f"❓ Total questions created: {stats['total_questions']}")
    
    if stats['total_tests'] > 0:
        print(f"\n📚 Categories ({len(stats['categories'])}):")
        for category in sorted(stats['categories']):
            print(f"   • {category}")
        
        print(f"\n📅 Years ({len(stats['years'])}):")
        for year in sorted(stats['years']):
            print(f"   • {year}")
        
        print(f"\n📋 Sections ({len(stats['sections'])}):")
        for section in sorted(stats['sections']):
            print(f"   • {section}")

def verify_database():
    """Verify that data was loaded correctly"""
    
    print("\n" + "=" * 50)
    print("🔍 DATABASE VERIFICATION")
    print("=" * 50)
    
    # Get counts
    test_count = Test.query.count()
    question_count = Question.query.count()
    
    # Safely check for users
    try:
        from models.user import User
        user_count = User.query.count()
        print(f"👤 Users in database: {user_count}")
    except (ImportError, AttributeError):
        print(f"👤 Users in database: Not available")
    
    print(f"📊 Tests in database: {test_count}")
    print(f"📊 Questions in database: {question_count}")
    
    if test_count == 0:
        print("❌ No tests found in database!")
        return
    
    # Sample a few tests
    print("\n📝 Sample tests:")
    tests = Test.query.limit(3).all()
    for test in tests:
        q_count = len(test.questions)
        print(f"   • {test.name} ({test.category} - {test.year}): {q_count} questions")

def seed_users():
    """Seed users if needed"""
    try:
        from models.user import User
        
        # Check if users already exist
        if User.query.count() > 0:
            print("👤 Users already exist, skipping user seed")
            return
        
        print("👤 Seeding users...")
        
        # Add test users
        user1 = User(username='testuser1', email='test1@example.com')
        user1.set_password('password123')

        user2 = User(username='testuser2', email='test2@example.com')
        user2.set_password('password456')

        user3 = User(username='admin', email='admin@example.com')
        user3.set_password('adminpassword')

        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)
        db.session.commit()
        print("✅ Users seeded successfully!")
    except ImportError:
        print("⚠️ User model not available, skipping user seed")
    except Exception as e:
        print(f"❌ Error seeding users: {e}")
        db.session.rollback()

if __name__ == '__main__':
    # Run the full seed
    with app.app_context():
        seed_data()
        seed_users()