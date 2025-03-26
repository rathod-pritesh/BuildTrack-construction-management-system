from flask import Flask, render_template, url_for, redirect, request, session, flash, jsonify, Response
import pymysql
from functools import wraps
from datetime import datetime
# Import our database and models from the new models.py file
from models import db, User, Project, Attendance
# Import the admin blueprint
from admin_panel import admin_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = "secret_key"
    
    # Config SQL Alchemy
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:Pritesh%400712@localhost/buildtrack"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize the db with this app
    db.init_app(app)
    
    # Register blueprint
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app
app = create_app()


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user = db.session.get(User, session['user_id'])
    projects = Project.query.filter_by(user_id=user.id).all()

    active_projects = sum(1 for p in projects if p.status == "active")
    pending_projects = sum(1 for p in projects if p.status == "pending")
    completed_projects = sum(1 for p in projects if p.status == "completed")

    return render_template('dashboard.html', 
                            username=user.username, 
                            email=user.email,
                            active_projects=active_projects,
                            pending_projects=pending_projects,
                            completed_projects=completed_projects,
                            projects=projects,
                            )


@app.route('/projects')
@login_required
def projects():
    return render_template('projects.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if not user or not user.checkPassword(password):
            flash('Invalid email or password', 'error')
            return redirect(url_for('login'))

        session['user_id'] = user.id
        session['username'] = user.username
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmpassword')

        if not username or not email or not password:
            flash('All fields are required', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'error')
            return redirect(url_for('register'))

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already exists', 'error')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email)
        new_user.setPassword(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    app.run(debug=True)