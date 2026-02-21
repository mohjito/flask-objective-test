import json
import os
from app import app, db
from models.test import Test, Question
from models.result import TestResult

def seed_data():
    """Main function to seed the database with all JSON files"""
    
    with app.app_context():
        print("🚀 Starting database seeding process...")
        print("=" * 50)
        
        # Drop and recreate all tables
        print("🔄 Recreating database schema...")
        db.drop_all()
        db.create_all()
        print("✅ Database schema recreated successfully!")
        
        # Set your data directory path
        data_dir = r'D:\my testbook\flask_objective_test\data'
        
        if not os.path.exists(data_dir):
            print(f"❌ Data directory not found: {data_dir}")
            print("Please create the directory and add JSON files first.")
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
        
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.endswith('.json'):
                    json_files_found = True
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, data_dir)
                    print(f"\n📄 Processing: {relative_path}")
                    
                    success = process_json_file(file_path, stats)
                    
                    if success:
                        stats['files_processed'] += 1
                    else:
                        stats['files_failed'] += 1
        
        if not json_files_found:
            print(f"\n❌ No JSON files found in {data_dir}")
            print("Please add some JSON files first.")
            return
        
        # Commit all changes to database
        try:
            db.session.commit()
            print(f"\n✅ Successfully committed all changes to database!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error committing to database: {e}")
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
                    continue
                
                question = Question(
                    question=q_data['question'],
                    question_hindi=q_data.get('question_hindi', q_data['question']),
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
    
    print(f"\n📚 Categories ({len(stats['categories'])}):")
    for category in sorted(stats['categories']):
        test_count = Test.query.filter_by(category=category).count()
        question_count = db.session.query(Question).join(Test).filter(Test.category == category).count()
        print(f"   • {category}: {test_count} tests, {question_count} questions")
    
    print(f"\n📅 Years ({len(stats['years'])}):")
    for year in sorted(stats['years']):
        test_count = Test.query.filter_by(year=year).count()
        print(f"   • {year}: {test_count} tests")
    
    print(f"\n📋 Sections ({len(stats['sections'])}):")
    for section in sorted(stats['sections']):
        test_count = Test.query.filter_by(section=section).count()
        print(f"   • {section}: {test_count} tests")

def verify_database():
    """Verify that data was loaded correctly"""
    
    print("\n" + "=" * 50)
    print("🔍 DATABASE VERIFICATION")
    print("=" * 50)
    
    # Get counts
    test_count = Test.query.count()
    question_count = Question.query.count()
    
    print(f"📊 Total tests in database: {test_count}")
    print(f"📊 Total questions in database: {question_count}")
    
    if test_count == 0:
        print("❌ No tests found in database!")
        return
    
    if question_count == 0:
        print("❌ No questions found in database!")
        return
    
    # Sample a few tests
    print("\n📝 Sample tests:")
    tests = Test.query.limit(3).all()
    for test in tests:
        q_count = len(test.questions)
        print(f"   • {test.name}: {q_count} questions")
    
    # Check bilingual data
    hindi_questions = Question.query.filter(Question.question_hindi.isnot(None)).count()
    hindi_options = Question.query.filter(Question.options_hindi.isnot(None)).count()
    
    print(f"\n🌐 Bilingual Data:")
    print(f"   • Questions with Hindi: {hindi_questions}/{question_count} ({hindi_questions/question_count*100:.1f}%)")
    print(f"   • Options with Hindi: {hindi_options}/{question_count} ({hindi_options/question_count*100:.1f}%)")
    
    # Check category distribution
    print("\n📊 Category Distribution:")
    categories = db.session.query(Test.category).distinct().all()
    for cat in categories:
        if cat[0]:
            count = Test.query.filter_by(category=cat[0]).count()
            print(f"   • {cat[0]}: {count} tests")

def clear_database():
    """Clear all data from database (optional helper function)"""
    
    with app.app_context():
        confirm = input("⚠️  This will delete ALL data. Are you sure? (yes/no): ")
        if confirm.lower() == 'yes':
            db.drop_all()
            db.create_all()
            print("✅ Database cleared successfully!")
        else:
            print("❌ Operation cancelled.")

if __name__ == '__main__':
    # You can add command line arguments if needed
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--clear':
            clear_database()
        elif sys.argv[1] == '--verify':
            with app.app_context():
                verify_database()
        else:
            print("Usage: python seed_data.py [--clear|--verify]")
    else:
        seed_data()