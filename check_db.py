from app import app
from models.test import Test

with app.app_context():
    tests = Test.query.limit(10).all()
    for t in tests:
        print(f"ID: {t.id}, Name: {t.name}, Category: {t.category}, Year: {t.year}")
