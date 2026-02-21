from datetime import datetime
from models import db

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)
    answers_data = db.Column(db.JSON, nullable=True) # To store user responses
    
    # Relationships
    user = db.relationship('User', backref=db.backref('results', lazy=True))
    test = db.relationship('Test', backref=db.backref('results', lazy=True))
