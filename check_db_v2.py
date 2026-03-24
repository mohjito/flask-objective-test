from app import app
from models.test import Test

with app.app_context():
    print("--- First 10 tests ---")
    tests = Test.query.all()
    for t in tests[:10]:
        print(f"ID: {t.id:3} | Name: {t.name[:40]:40} | Cat: {t.category:5} | Year: {t.year}")
    
    print("\n--- Search for 'htet' in Name ---")
    htet_tests = Test.query.filter(Test.name.ilike('%htet%')).all()
    for t in htet_tests:
        print(f"ID: {t.id:3} | Name: {t.name[:40]:40} | Cat: {t.category:5} | Year: {t.year}")

    print("\n--- Search for 'ctet' in Name ---")
    ctet_tests = Test.query.filter(Test.name.ilike('%ctet%')).all()
    for t in ctet_tests:
        print(f"ID: {t.id:3} | Name: {t.name[:40]:40} | Cat: {t.category:5} | Year: {t.year}")
