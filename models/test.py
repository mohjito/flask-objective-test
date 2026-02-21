from models import db

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='General') # e.g. PRT, TGT, PGT
    year = db.Column(db.Integer, nullable=False, default=2024)
    section = db.Column(db.String(50), nullable=False, default='Full Paper') # e.g. Hindi, English, Pedagogy
    duration = db.Column(db.Integer, default=10) # Duration in minutes
    questions = db.relationship('Question', backref='test', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False) # English
    question_hindi = db.Column(db.String(500), nullable=True) # Hindi
    options = db.Column(db.JSON, nullable=False) # English options
    options_hindi = db.Column(db.JSON, nullable=True) # Hindi options
    correct_answer = db.Column(db.String(100), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
