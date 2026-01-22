from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Enum
db = SQLAlchemy()

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def setPassword(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def checkPassword(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)    

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    projects = db.relationship('Project', backref='user', lazy=True)
    is_approved = db.Column(db.Boolean, default=False)

    def setPassword(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def checkPassword(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

class PendingUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    def setPassword(self, password):
        self.password_hash = generate_password_hash(password)

    def checkPassword(self, password):
        return check_password_hash(self.password_hash, password)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    client_id = db.Column(db.Integer, nullable=False)
    manager_id = db.Column(db.Integer, nullable=False)
    budget = db.Column(db.Float, nullable=False)
    project_location = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(Enum('active', 'pending','completed','archived',name='project_status'))  # active, pending, completed

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    attendance_date = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    attendance_status = db.Column(db.String(10), nullable=False)  # Present, Absent, Leave
    check_in_time = db.Column(db.Time, nullable=True)
    check_out_time = db.Column(db.Time, nullable=True)
    work_hours = db.Column(db.Float, default=0.0, nullable=True)
    overtime_hours = db.Column(db.Float, default=0.0, nullable=True)

class Archive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    project_location = db.Column(db.String(255), nullable=False)
    archive_reason = db.Column(db.String(50), nullable=False)
    archive_notes = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=False)
    budget = db.Column(db.Float, nullable=False)
    archived_date = db.Column(db.DateTime, default=datetime.utcnow(), nullable=False)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Who uploaded the report
    is_admin_upload = db.Column(db.Boolean, default=False)  # Whether uploaded by admin or user
    uploader = db.relationship('User', backref='reports', lazy=True)

class MemberReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # User who uploaded
    status = db.Column(db.String(20), default='pending')  # Status: pending, approved, rejected
    user = db.relationship('User', backref='member_reports', lazy=True)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    subject = db.Column(db.String(100))
    message = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow())
