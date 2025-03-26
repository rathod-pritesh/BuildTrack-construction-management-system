from flask import Blueprint, render_template, redirect, request, session, flash, url_for
from functools import wraps
from models import db, User, Project

admin_bp = Blueprint('admin', __name__, template_folder='templates')

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('admin_logged_in') != True:
            flash('Admin access required!', 'error')
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def ensure_unassigned_user():
    """Ensure that an 'Unassigned' user exists and return it."""
    unassigned_user = User.query.filter_by(email="unassigned@example.com").first()

    if not unassigned_user:
        try:
            new_user = User(username="Unassigned", email="unassigned@example.com", password_hash="")
            db.session.add(new_user)
            db.session.commit()
            return new_user
        except Exception as e:
            db.session.rollback()  # Rollback if an error occurs
            print(f"Error creating 'Unassigned' user: {e}")
            return None

    return unassigned_user


@admin_bp.route('/')
def admin_home():
    return redirect(url_for('admin.admin_login'))  

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        if username == "admin" and password == "admin":
            session['admin_logged_in'] = True
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('Invalid admin credentials', 'error')
    return render_template('admin_login.html')

@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard():
    projects = Project.query.all()
    users = User.query.all()
    return render_template('admin_dashboard.html', projects=projects,users=users)

@admin_bp.route('/logout')
@admin_required
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Admin logged out successfully!', 'info')
    return redirect(url_for('admin.admin_login'))

@admin_bp.route('/add_project', methods=['POST'])
@admin_required
def admin_add_project():
    name = request.form.get('name')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    client_id = request.form.get('client_id')
    manager_id = request.form.get('manager_id')
    budget = request.form.get('budget')
    project_location = request.form.get('project_location')
    description = request.form.get('description')
    status = request.form.get('status')
    assigned_user_email = request.form.get('assigned_user_email')

    if not assigned_user_email:
        flash("User email is required to assign the project", "error")
        return redirect(url_for('admin.admin_dashboard'))

    user = User.query.filter_by(email=assigned_user_email).first()
    if not user:
        flash("No user found with this email", "error")
        return redirect(url_for('admin.admin_dashboard'))

    new_project = Project(
        name=name, 
        start_date=start_date, 
        end_date=end_date,
        client_id=client_id, 
        manager_id=manager_id, 
        budget=budget,
        project_location=project_location, 
        description=description,
        status=status, 
        user_id=user.id
    )
    db.session.add(new_project)
    db.session.commit()

    flash(f"Project assigned to {assigned_user_email} successfully!", "success")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/remove_project', methods=['POST'])
@admin_required
def admin_remove_project():
    project_id = request.form.get('project_id')
    project = Project.query.get(project_id)

    if project:
        user = User.query.get(project.user_id)
        email = user.email if user else "unknown user"
        
        flash(f"Project '{project.name}' assigned to {email} has been removed", "info")
        db.session.delete(project)
        db.session.commit()
    else:
        flash("Project not found", "error")

    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/add_user', methods=['POST'])
@admin_required
def admin_add_user():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    if not username or not email or not password:
        flash('All fields are required', 'error')
        return redirect(url_for('admin.admin_dashboard'))

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('User with this email already exists!', 'error')
        return redirect(url_for('admin.admin_dashboard'))

    new_user = User(username=username, email=email)
    new_user.setPassword(password)
    db.session.add(new_user)
    db.session.commit()

    flash('User added successfully!', 'success')
    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/remove_user', methods=['POST'])
@admin_required
def admin_remove_user():
    user_id = request.form.get('user_id')
    user = User.query.get(user_id)

    if user:
        # Get or create "Unassigned" user
        default_user = ensure_unassigned_user()
        
        if not default_user:
            flash("Error: Could not assign projects to 'Unassigned' user.", "error")
            return redirect(url_for('admin.admin_dashboard'))

        # Update all projects to be assigned to "Unassigned"
        Project.query.filter_by(user_id=user.id).update({Project.user_id: default_user.id})

        db.session.delete(user)
        db.session.commit()

        flash('User removed successfully! Projects reassigned to "Unassigned".', 'success')
    else:
        flash('User not found!', 'error')

    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/reassign_project', methods=['POST'])
@admin_required
def admin_reassign_project():
    project_id = request.form.get('project_id')
    new_user_email = request.form.get('new_user_email')

    project = Project.query.get(project_id)
    new_user = User.query.filter_by(email=new_user_email).first()

    if not project:
        flash("Project not found!", "error")
        return redirect(url_for('admin.admin_dashboard'))

    if not new_user:
        flash("User not found with that email!", "error")
        return redirect(url_for('admin.admin_dashboard'))

    project.user_id = new_user.id
    db.session.commit()

    flash(f"Project reassigned to {new_user_email} successfully!", "success")
    return redirect(url_for('admin.admin_dashboard'))
