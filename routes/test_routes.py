from flask import Blueprint, request, render_template, redirect, url_for, flash
from models.test import Test, Question, ExamVote, db
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
    
@test_routes.route('/select_exam_type/<category>', methods=['GET'])
def select_exam_type(category):
    # Options requested by user
    exam_types = ['htet', 'ctet', 'kvs', 'nvs', 'Emrs', 'Dssb']
    
    # Check which exam types actually have tests in the DB for this category
    available_types = db.session.query(Test.exam_type).filter_by(category=category).distinct().all()
    available_types = [t[0].lower() for t in available_types if t[0]]
    
    return render_template('select_exam_type.html', 
                           category=category, 
                           exam_types=exam_types,
                           available_types=available_types)

@test_routes.route('/vote_exam_type/<category>/<exam_type>', methods=['POST'])
def vote_exam_type(category, exam_type):
    # Persist the vote in the database
    vote = ExamVote.query.filter_by(category=category, exam_type=exam_type.lower()).first()
    
    if vote:
        vote.vote_count += 1
    else:
        vote = ExamVote(category=category, exam_type=exam_type.lower(), vote_count=1)
        db.session.add(vote)
    
    db.session.commit()
    
    flash(f'Thanks for your vote! We will prioritize uploading {exam_type.upper()} tests for {category}. (Current votes: {vote.vote_count})', 'success')
    return redirect(url_for('test_routes.select_exam_type', category=category))

@test_routes.route('/admin/votes')
def view_votes():
    # Only show this to admin (for now, everyone who knows the URL)
    votes = ExamVote.query.order_by(ExamVote.vote_count.desc()).all()
    return render_template('view_votes.html', votes=votes)

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

@test_routes.route('/select_year/<category>/<exam_type>', methods=['GET'])
def select_year(category, exam_type):
    # Get unique years for the category and exam_type
    years = db.session.query(Test.year).filter_by(category=category, exam_type=exam_type).distinct().order_by(Test.year.desc()).all()
    years = [y[0] for y in years if y[0]]  # Filter out None values
    return render_template('select_year.html', category=category, exam_type=exam_type, years=years)

@test_routes.route('/select_paper/<category>/<exam_type>/<int:year>', methods=['GET'])
def select_paper(category, exam_type, year):
    tests = Test.query.filter_by(category=category, exam_type=exam_type, year=year).all()
    return render_template('select_paper.html', category=category, exam_type=exam_type, year=year, tests=tests)

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
            'serial_no': question.serial_no,
            'question': question.question,
            'question_hindi': question.question_hindi,
            'passage': question.passage,
            'passage_hindi': question.passage_hindi,
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