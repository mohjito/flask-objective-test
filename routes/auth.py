from flask import Blueprint, request, render_template, redirect, url_for, flash
from models.user import User, db
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user, login_required, current_user

auth = Blueprint('auth', __name__)

# Render the index page (landing page)
@auth.route('/', methods=['GET'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('test_routes.dashboard'))
    return render_template('index.html')

# Register a new user
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
        
    data = request.form
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if User.query.filter_by(username=username).first():
        flash("Username already exists!", "error")
        return redirect(url_for('auth.register'))

    if User.query.filter_by(email=email).first():
        flash("Email already exists!", "error")
        return redirect(url_for('auth.register'))

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    flash("User registered successfully! Please login.", "success")
    return redirect(url_for('auth.login'))

# Login the user
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    data = request.form
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        login_user(user)
        flash("Login successful!", "success")
        return redirect(url_for('test_routes.dashboard'))
    else:
        flash("Invalid username or password", "error")
        return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('auth.index'))

