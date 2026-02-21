from flask import Blueprint, request, render_template, redirect, url_for, flash
from models.test import Test, Question, db
from models.result import TestResult
from flask_login import login_required, current_user

# Define the Blueprint
test_routes = Blueprint('test_routes', __name__)

@test_routes.route('/dashboard', methods=['GET'])
def dashboard():
    # Get unique categories
    categories = db.session.query(Test.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]  # Filter out None values
    return render_template('dashboard.html', categories=categories)

@test_routes.route('/donate')
def donate():
    return render_template('donate.html')

@test_routes.route('/profile', methods=['GET'])
@login_required
def profile():
    # Get user's test history
    results = TestResult.query.filter_by(user_id=current_user.id)\
        .order_by(TestResult.date_taken.desc()).all()
    return render_template('profile.html', results=results)

@test_routes.route('/select_year/<category>', methods=['GET'])
def select_year(category):
    # Get unique years for the category
    years = db.session.query(Test.year).filter_by(category=category).distinct().order_by(Test.year.desc()).all()
    years = [y[0] for y in years if y[0]]  # Filter out None values
    return render_template('select_year.html', category=category, years=years)

@test_routes.route('/select_paper/<category>/<int:year>', methods=['GET'])
def select_paper(category, year):
    tests = Test.query.filter_by(category=category, year=year).all()
    return render_template('select_paper.html', category=category, year=year, tests=tests)

@test_routes.route('/take_test/<int:test_id>', methods=['GET'])
def take_test(test_id):
    test = Test.query.get_or_404(test_id)
    # Don't pass timer_enabled from URL anymore - we'll use the modal
    return render_template('test_page.html', test=test)

@test_routes.route('/submit_test/<int:test_id>', methods=['POST'])
def submit_test(test_id):
    test = Test.query.get_or_404(test_id)
    score = 0
    total_questions = len(test.questions)
    results = []

    for question in test.questions:
        user_answer = request.form.get(str(question.id))
        is_correct = user_answer == question.correct_answer
        if is_correct:
            score += 1
        
        results.append({
            'question': question.question,
            'question_hindi': question.question_hindi,
            'options': question.options,
            'options_hindi': question.options_hindi,
            'user_answer': user_answer,
            'correct_answer': question.correct_answer,
            'is_correct': is_correct
        })
    
    # Save Result with answers_data snapshot - ONLY IF LOGGED IN
    if current_user.is_authenticated:
        test_result = TestResult(
            user_id=current_user.id,
            test_id=test.id,
            score=score,
            total_questions=total_questions,
            answers_data=results
        )
        db.session.add(test_result)
        db.session.commit()

    return render_template('result.html', test=test, score=score, total_questions=total_questions, results=results)

@test_routes.route('/view_result/<int:result_id>', methods=['GET'])
@login_required
def view_result(result_id):
    result = TestResult.query.get_or_404(result_id)
    if result.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('test_routes.dashboard'))
    
    return render_template('result.html', 
                           test=result.test, 
                           score=result.score, 
                           total_questions=result.total_questions, 
                           results=result.answers_data,
                           is_review=True)