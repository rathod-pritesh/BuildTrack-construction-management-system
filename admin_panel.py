from flask import Blueprint, render_template, redirect, request, session, flash, url_for, current_app
from functools import wraps
from models import db,Admin, User,PendingUser, Project, Archive, Report, MemberReport, ContactMessage, Attendance
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from zoneinfo import ZoneInfo
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

@admin_bp.route('/approve_pending_user', methods=['POST'])
@admin_required
def approve_pending_user():
    pending_id = request.form.get('pending_id')
    pending = PendingUser.query.get(pending_id)

    if pending:
        new_user = User(username=pending.username, email=pending.email, password_hash=pending.password_hash, is_approved=True)
        db.session.add(new_user)
        db.session.delete(pending)
        db.session.commit()
        flash(f"User '{new_user.username}' approved successfully!", 'success')
    else:
        flash('Pending ser not found','error')

    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/decline_pending_user', methods=['POST'])
@admin_required
def decline_pending_user():
    pending_id = request.form.get('pending_id')
    pending = PendingUser.query.get(pending_id)

    if pending:
        db.session.delete(pending)
        db.session.commit()
        flash(f"User '{pending.username}' declined and removed from pending list.", 'warning')
    else:
        flash('Pending user not found', 'error')

    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/upload_report', methods=['POST'])
def upload_report():
    if 'report_file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.referrer)
        
    file = request.files['report_file']
    
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(request.referrer)
        
    if file and file.filename.endswith('.pdf'):
        # Check file size (10MB limit)
        file.seek(0, 2)  
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        if file_size > 10 * 1024 * 1024:  # 10MB in bytes
            flash('File size exceeds the 10MB limit', 'danger')
            return redirect(request.referrer)
        
        # Get form data
        title = request.form.get('report_title', '').strip()
        description = request.form.get('report_description', '').strip()

        if not title:
            flash('Report title is required', 'danger')
            return redirect(request.referrer)

        filename = secure_filename(file.filename)
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        try:
            file.save(file_path)
            report = Report(
                title=title,
                description=description,
                file_path=file_path,
                original_filename=filename,
                upload_date=datetime.utcnow(),
                is_admin_upload = True
            )

            db.session.add(report)
            db.session.commit()

            flash('Report uploaded successfully', 'success')
            return redirect(url_for('admin.admin_dashboard'))

        except Exception as e:
            db.session.rollback()
            if os.path.exists(file_path):
                os.remove(file_path)
            current_app.logger.error(f"Error saving report: {str(e)}")
            flash(f'Error saving report to database: {str(e)}', 'danger')
            return redirect(request.referrer)
    else:
        flash('Only PDF files are allowed', 'danger')
        return redirect(request.referrer)

@admin_bp.route('/delete_report', methods=['POST'])
@admin_required
def delete_report():
    report_id = request.form.get('report_id')
    if not report_id:
        flash('Report ID is required', 'danger')
        return redirect(request.referrer)
    
    report = Report.query.get(report_id)
    if not report:
        flash('Report not found', 'danger')
        return redirect(request.referrer)
    
    try:
        # Delete the physical file if it exists
        if report.file_path and os.path.exists(report.file_path):
            os.remove(report.file_path)
        
        # Delete database record
        db.session.delete(report)
        db.session.commit()
        
        flash('Report deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting report: {str(e)}")
        flash(f'Error deleting report: {str(e)}', 'danger')
    
    return redirect(request.referrer)

#Admin approve or reject member reoport
@admin_bp.route('/member_reports')
@admin_required
def member_reports():
    member_reports = MemberReport.query.order_by(MemberReport.upload_date.desc()).all()
    return render_template('admin_member_reports.html', member_reports=member_reports)

@admin_bp.route('/approve_member_report/<int:report_id>', methods=['POST'])
@admin_required
def approve_member_report(report_id):
    report = MemberReport.query.get_or_404(report_id)
    report.status = 'approved'
    db.session.commit()
    flash('Member report approved', 'success')
    return redirect(url_for('admin.member_reports'))

@admin_bp.route('/reject_member_report/<int:report_id>', methods=['POST'])
@admin_required
def reject_member_report(report_id):
    report = MemberReport.query.get_or_404(report_id)
    report.status = 'rejected'
    db.session.commit()
    flash('Member report rejected', 'success')
    return redirect(url_for('admin.member_reports'))

def ensure_unassigned_user():
    """Ensure that an 'Unassigned' user exists and return it."""
    unassigned_user = User.query.filter_by(email="buildtrack2022@gmail.com").first()

    if not unassigned_user:
        try:
            new_user = User(username="Unassigned", email="buildtrack2022@gmail.com", password_hash="")
            db.session.add(new_user)
            db.session.commit()
            return new_user
        except Exception as e:
            db.session.rollback()  
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

        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.checkPassword(password):
            session['admin_logged_in'] = True
            flash('Admin login successful','success')
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('Invalid admin credentials', 'error')
        
    return render_template('admin_login.html')

@admin_bp.route('/change_password', methods=['GET', 'POST'])
@admin_required
def admin_change_password():
    if request.method == 'POST':
        username = session.get('admin_username', 'admin') 
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        admin = Admin.query.filter_by(username=username).first()

        if not admin or not admin.checkPassword(current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('admin.admin_change_password'))

        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('admin.admin_change_password'))

        admin.setPassword(new_password)
        db.session.commit()
        flash('Password changed successfully!', 'success')
        return redirect(url_for('admin.admin_dashboard'))

    return render_template('admin_change_password.html')


@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard():
    projects = Project.query.all()
    users = User.query.all()
    reports = Report.query.filter_by(is_admin_upload=True).order_by(Report.upload_date.desc()).all()
    member_reports = MemberReport.query.order_by(MemberReport.upload_date.desc()).all()
    contact_messages = ContactMessage.query.order_by(ContactMessage.submitted_at.desc()).all()
    pending_users= PendingUser.query.order_by(PendingUser.registered_at.desc()).all()

    return render_template('admin_dashboard.html', projects=projects,
                                                    users=users, 
                                                    reports=reports,
                                                    contact_messages=contact_messages,
                                                    pending_users=pending_users, 
                                                    member_reports=member_reports
                                                    )

@admin_bp.route('/projects')
@admin_required
def admin_projects():
    projects = Project.query.all()
    users = User.query.all()
    return render_template('admin_projects.html', projects=projects, users=users)

@admin_bp.route('/users')
@admin_required
def admin_users():
    users = User.query.all()
    pending_users = PendingUser.query.order_by(PendingUser.registered_at.desc()).all()

    attendance_summary = {}
    for user in users:
        last = Attendance.query.filter_by(username=user.username).order_by(Attendance.attendance_date.desc()).first()
        total_present = Attendance.query.filter_by(username=user.username, attendance_status='present').count()
        attendance_summary[user.username] = {
            'last': last,
            'present_days': total_present
        }
    
    return render_template('admin_users.html', users=users, pending_users=pending_users, summaries=attendance_summary)

@admin_bp.route('/reports')
@admin_required
def admin_reports():
    reports = Report.query.filter_by(is_admin_upload=True).all()
    member_reports = MemberReport.query.all()
    return render_template('admin_reports.html', reports=reports, member_reports=member_reports)

@admin_bp.route('/contacts')
@admin_required
def admin_contacts():
    contact_messages = ContactMessage.query.order_by(ContactMessage.submitted_at.desc()).all()

    for msg in contact_messages:
        msg.local_submitted_at = msg.submitted_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Kolkata"))
    return render_template('admin_contacts.html', contact_messages=contact_messages)

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
    assigned_user_id = request.form.get('assigned_user_id')

    if not assigned_user_id:
        flash("User must be selected to assign the project", "error")
        return redirect(url_for('admin.admin_dashboard'))

    user = User.query.get(assigned_user_id)
    if not user:
        flash("Selected user not found", "error")
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

    flash(f"Project '{name}' assigned to {user.username} successfully!", "success")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/archive_project', methods=['POST'])
@admin_required
def admin_archive_project():
    project_id = request.form.get('project_id')
    archive_reason = request.form.get('archive_reason')
    archive_notes = request.form.get('archive_notes')
    
    project = Project.query.get(project_id)

    if project:
        # Update project to archived status
        new_archive = Archive(
            project_id=project.id,
            project_location=project.project_location,
            archive_reason=archive_reason,
            archive_notes=archive_notes,
            description=project.description,
            budget=project.budget,
            archived_date=datetime.now()
        )
        
        db.session.add(new_archive)

        project.status = 'archived'

        db.session.commit()

        user = User.query.get(project.user_id)
        email = user.email if user else "unknown user"

        flash(f"Project '{project.name}' assigned to {email} has been archived", "info")
    else:
        flash("Project not found", "error")

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

        # Update all projects and member reports to be assigned to "Unassigned"
        Project.query.filter_by(user_id=user.id).update({Project.user_id: default_user.id})

        MemberReport.query.filter_by(user_id=user.id).update({MemberReport.user_id: default_user.id})
        db.session.delete(user)
        db.session.commit()

        flash('User removed successfully! Projects and reports reassigned to "Unassigned".', 'success')
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

    flash(f"Project reassigned to {new_user.username} successfully!", "success")
    return redirect(url_for('admin.admin_dashboard'))
