from flask import Flask, render_template, url_for, redirect, request, session, flash, jsonify, Response, current_app
import pymysql
from functools import wraps
from datetime import datetime, date, time, timedelta
import os
import cv2
import numpy as np
import face_recognition
import time as time_module
import random
import smtplib
import uuid
from werkzeug.utils import secure_filename
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from models import db, User,PendingUser, Project, Attendance, Archive, Report, MemberReport, ContactMessage
# Import the admin blueprint
from admin_panel import admin_bp


def create_app():
    app = Flask(__name__)
    baseDir = os.path.abspath(os.path.dirname(__file__))
    app.secret_key = "secret_key"
    
    # Config SQL Alchemy
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:Pritesh%400712@localhost/buildtrack"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads', 'reports')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize the db with this app
    db.init_app(app)
    
    # Register blueprint
    app.register_blueprint(admin_bp, url_prefix='/admin')

    @app.route('/check_detection', endpoint='check_detection')
    def check_detection():
        if 'DETECTED_NAME' in app.config:
            name = app.config['DETECTED_NAME']
            attendance_type = app.config.get('ATTENDANCE_TYPE', 'check_in')
        
            # Process attendance
            attendance_message = mark_attendance_record(name, attendance_type)
        
            # Store in session for flash message
            session['attendance_message'] = attendance_message
            session['attendance_success'] = 'success' if 'successful' in attendance_message.lower() else 'error'
        
            # Clean up
            del app.config['DETECTED_NAME']
            if 'ATTENDANCE_TYPE' in app.config:
                del app.config['ATTENDANCE_TYPE']
        
            return jsonify({'detected': True, 'name': name, 'redirect': url_for('dashboard')})
        else:
            return jsonify({'detected': False})

    return app


app = create_app()

camera =None
face_encodings =[]
face_names = []


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def load_face_encodings():
    global face_encodings, face_names
    path ='static/faces'
    images =[]
    classNames =[]

    if not os.path.exists(path):
        os.makedirs(path)
        return [],[]

    myList = os.listdir(path)

    for cl in myList:
        curImg = cv2.imread(f'{path}/{cl}')
        if curImg is not None:
            images.append(curImg)
            name = os.path.splitext(cl)[0]
            classNames.append(name)

    face_encodings =[]
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        try:
            encode = face_recognition.face_encodings(img)[0]
            face_encodings.append(encode)
        except IndexError:
            continue

    face_names =classNames
    return face_encodings, face_names

def mark_attendance_record(username, attendance_type):
    current_date = datetime.now().date()
    current_time = datetime.now().time()

    user = User.query.filter_by(username=username).first()
    if not user:
        return f"Error: No registered user found with the name '{username}'"

    record = Attendance.query.filter_by(
        username=username,
        attendance_date=current_date
    ).first()

    if attendance_type == 'check_in':
        if record is None:
            new_attendance = Attendance(
                username=username,
                attendance_date=current_date,  
                attendance_status='present',
                check_in_time=current_time,
                check_out_time=None,
                work_hours=0.0,
                overtime_hours=0.0
            )
            db.session.add(new_attendance)
            db.session.commit()
            return f"Check-in successful for {username} at {current_time.strftime('%H:%M:%S')}"
        else:
            return f"{username}, already checked in at {record.check_in_time.strftime('%H:%M:%S')}"

    if attendance_type == 'check_out':
        if record is None:
            return f"{username}, please check in first."

        if record.check_out_time:
            return f"{username}, you have already checked out today at {reocrd.check_out_time.strftime('%H:%M:%S')}"

        record.check_out_time = current_time
        check_in_datetime = datetime.combine(current_date, record.check_in_time)
        check_out_datetime = datetime.combine(current_date, current_time)
        duration = check_out_datetime - check_in_datetime
        hours_worked = duration.total_seconds()/3600

        record.work_hours = min(hours_worked, 8.0)
        record.overtime_hours = max(0, hours_worked - 8.0)

        db.session.commit()
        return f"Check-out successful for {username}. Worked {hours_worked:.2f} hours."

def generate_frames(attendance_type=None):
    global camera, face_encodings, face_names

    if attendance_type is None:
        attendance_type = 'check_in'

    if camera and camera.isOpened():
        camera.release()
    camera = cv2.VideoCapture(0)

    if not face_encodings:
        face_encodings, face_names = load_face_encodings()

    frame_count = 0
    detected_name = None

    while True:
        success, frame = camera.read()
        if not success:
            break
        
        frame_count += 1
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_small_frame)
        current_face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations) 
        
        for face_encoding in current_face_encodings:
            matches = face_recognition.compare_faces(face_encodings, face_encoding)
            name = "Unknown"

            if True in matches:
                face_distances = face_recognition.face_distance(face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = face_names[best_match_index]

                    if name!= "Unknown":
                        detected_name = name
                        # Draw a rectangle around the face with the name
                        y1, x2, y2, x1 = face_locations[0]
                        y1, x2, y2, x1 = y1*4, x2*4, y2*4, x1*4  # Scale back up
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, name, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame +b'\r\n')

        if detected_name:
            app.config['DETECTED_NAME'] = detected_name
            app.config['ATTENDANCE_TYPE'] = attendance_type
            time_module.sleep(2)
            break

    if camera and camera.isOpened():
        camera.release()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user = db.session.get(User, session['user_id'])
    
    projects = Project.query.filter_by(user_id=user.id).all()

    records = Attendance.query.filter_by(username=user.username).order_by(Attendance.attendance_date.desc()).all()

    active_projects = sum(1 for p in projects if p.status == "active")
    pending_projects = sum(1 for p in projects if p.status == "pending")
    completed_projects = sum(1 for p in projects if p.status == "completed")

    admin_reports = Report.query.filter_by(is_admin_upload=True).order_by(Report.upload_date.desc()).all()
    member_reports = MemberReport.query.filter_by(user_id=user.id).order_by(MemberReport.upload_date.desc()).all()
    
    if 'attendance_message' in session:
        if session.get('attendance_success', True):
            flash(session['attendance_message'], 'success')
        else:
            flash(session['attendance_message'], 'error')
        session.pop('attendance_message')
        session.pop('attendance_success', None)


    return render_template('dashboard.html', 
                            username=user.username, 
                            email=user.email,
                            active_projects=active_projects,
                            pending_projects=pending_projects,
                            completed_projects=completed_projects,
                            projects=projects,
                            records=records,
                            admin_reports=admin_reports,
                            member_reports=member_reports,
                            )

@app.route('/upload_member_report', methods=['POST'])
@login_required
def upload_member_report():
    user = db.session.get(User, session['user_id'])

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
        file.seek(0)
        
        if file_size > 10 * 1024 * 1024:
            flash('File size exceeds the 10MB limit', 'danger')
            return redirect(request.referrer)
        
        title = request.form.get('report_title', '').strip()
        description = request.form.get('report_description', '').strip()

        if not title:
            flash('Report title is required', 'danger')
            return redirect(request.referrer)

        filename = secure_filename(file.filename)
        member_reports_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'member_reports')
        os.makedirs(member_reports_folder, exist_ok=True)
        file_path = os.path.join(member_reports_folder, filename)

        try:
            file.save(file_path)
            report = MemberReport(
                title=title,
                description=description,
                file_path=file_path,
                original_filename=filename,
                upload_date=datetime.utcnow(),
                user_id=user.id
            )

            db.session.add(report)
            db.session.commit()

            flash('Report submitted successfully', 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            db.session.rollback()
            if os.path.exists(file_path):
                os.remove(file_path)
            current_app.logger.error(f"Error saving report: {str(e)}")
            flash(f'Error saving report: {str(e)}', 'danger')
            return redirect(request.referrer)
    else:
        flash('Only PDF files are allowed', 'danger')
        return redirect(request.referrer)

@app.route('/delete_member_report', methods=['POST'])
@login_required
def delete_member_report():
    report_id = request.form.get('report_id')
    if not report_id:
        flash('Report ID is required', 'danger')
        return redirect(request.referrer)
    
    user = db.session.get(User, session['user_id'])

    report = MemberReport.query.filter_by(id=report_id, user_id=user.id).first()
    
    if not report:
        flash('Report not found or you do not have permission to delete it', 'danger')
        return redirect(request.referrer)
    
    try:
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

@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    message = request.form.get('message')

    new_msg = ContactMessage(
        name=name,
        email=email,
        subject=subject,
        message=message
    )

    db.session.add(new_msg)
    db.session.commit()

    flash("Message sent successfully!","success")
    return redirect(url_for('contact'))

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if user.checkPassword(password):
                if not user.is_approved:
                    flash("Your account is pending admin approval.",'warning')
                    return redirect(url_for('login'))

                session['user_id'] = user.id
                session['username'] = user.username
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))

            else:
                flash('Invalid email or password', 'error')
                return redirect(url_for('login'))

        
        pending_user = PendingUser.query.filter_by(email=email).first()
        if pending_user:
            if pending_user.checkPassword(password):
                flash("Your registration is still pending admin approval.", 'warning')
            else:
                flash('Invalid email or password', 'error')
            return redirect(url_for('login'))

        
        flash('Invalid email or password', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/change_password', methods=['GET', 'POST'], endpoint='user_change_password')
@login_required
def user_change_password():
    user = db.session.get(User, session['user_id'])

    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not user.checkPassword(current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('user_change_password'))

        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('user_change_password'))

        user.setPassword(new_password)
        db.session.commit()
        flash('Password changed successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('user_change_password.html')


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

        if PendingUser.query.filter_by(email=email).first() or User.query.filter_by(email=email).first():
            flash('Email already registered or pending approval', 'error')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'error')
            return redirect(url_for('register'))

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already exists', 'error')
            return redirect(url_for('register'))

        pending = PendingUser(username=username, email=email)
        pending.setPassword(password)
        db.session.add(pending)
        db.session.commit()

        flash('Registration submitted! Awaiting admin approval.', 'info')
        return redirect(url_for('login'))

    return render_template('register.html')

def send_otp_email(to_email, otp_code):
    EMAIL_ADDRESS = 'connect.buildtrack@gmail.com'
    EMAIL_PASSWORD = 'gpuyqanzpzccmjzo'

    try:
        html_content = f"""
        <html>
        <head>
            <style>
                .email-container {{
                    font-family: Arial, sans-serif;
                    padding: 20px;
                    background-color: #f8f8f8;
                }}
                .email-content {{
                    background-color: #ffffff;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                .otp-code {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin: 20px 0;
                }}
                .footer {{
                    font-size: 12px;
                    color: #888888;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="email-content">
                    <h2>🔐 OTP Verification - BuildTrack</h2>
                    <p>Hello,</p>
                    <p>You have requested to reset your password. Please use the OTP below to proceed:</p>
                    <div class="otp-code">{otp_code}</div>
                    <p>This OTP is valid for 5 minutes. Do not share it with anyone.</p>
                    <p>If you did not request this, please ignore this email.</p>
                    <div class="footer">
                        <p>BuildTrack Team<br>support@buildtrack.com</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart(f"Your OTP is: {otp_code}")
        msg['Subject'] = 'BuildTrack - OTP Verification'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email

        part_html = MIMEText(html_content,'html')
        msg.attach(part_html)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

        print("[+] OTP email sent successfully.")

    except Exception as e:
        print(f'[!] Email sending failed: {e}')
        raise

@app.route('/forgot-password', methods=['GET','POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Email not registered.','error')
            return redirect(url_for('forgot_password'))

        otp = str(random.randint(100000, 999999))
        session['reset_email'] = email
        session['otp'] = otp

        try:
            send_otp_email(email, otp)
            flash('OTP sent to your email.','info')

        except Exception as e:
            flash(f'Error sending OTP: {str(e)}',' error')
            return redirect(url_for('forgot_password'))

        return redirect(url_for('verify_otp'))
    
    return render_template('forgot_password.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        input_otp = request.form.get('otp')
        if input_otp == session.get('otp'):
            flash('OTP verified. Please reset your password.', 'success')
            return redirect(url_for('reset_password'))
        else:
            flash('Incorrect OTP.', 'error')
    return render_template('verify_otp.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('reset_password'))

        email = session.get('reset_email')
        user = User.query.filter_by(email=email).first()
        if user:
            user.setPassword(new_password)
            db.session.commit()
            session.pop('otp', None)
            session.pop('reset_email', None)
            flash('Password updated. Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('User not found.', 'error')

    return render_template('reset_password.html')

@app.route('/profile')
@login_required
def profile():
    user = db.session.get(User, session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/activity-log')
@login_required
def activity_log():
    user = db.session.get(User, session['user_id'])
    logs = [
        {"timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "action": "Logged in"},
        {"timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "action": "Viewed dashboard"},
    ]
    return render_template('activity_log.html', logs=logs)

@app.route('/account-settings', methods=['GET', 'POST'])
@login_required
def account_settings():
    user = db.session.get(User, session['user_id'])

    if request.method == 'POST':
        new_username = request.form.get('username').strip()

        if not new_username:
            flash('Username cannot be empty.', 'danger')
            return redirect(url_for('account_settings'))

        if new_username != user.username:
            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user:
                flash('Username already taken.', 'danger')
                return redirect(url_for('account_settings'))

            
            old_username = user.username
            user.username = new_username

            attendance_records = Attendance.query.filter_by(username=old_username).all()
            for record in attendance_records:
                record.username = new_username

            session['username'] = new_username  

            try:
                db.session.commit()
                flash('Username updated successfully.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating username: {str(e)}', 'danger')
        else:
            flash('No changes made to username.', 'info')

        return redirect(url_for('account_settings'))

    return render_template('account_settings.html', user=user)

@app.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.get_json()
    msg = data.get("message", "").lower()

    if "hii" in msg or "hello" in msg:
        reply = "Hello 👷‍♂️ How can I help you?"
    elif "attendance" in msg:
        reply = "You can check attendance in the Attendance section 📸"
    elif "project" in msg:
        reply = "Project details are under Projects tab 📊"
    elif "material" in msg:
        reply = "Material stock is in Materials section 🧱"
    elif "name" in msg:
        reply = "My name is BuildBot.An assistant which can helps you to solve your any query."
    elif "bye" in msg or "end" in msg:
        reply = "Have a great day!"
    else:
        reply = "Sorry, I didn’t understand. Try asking about attendance, projects, or materials."
    
    return jsonify({"reply": reply})

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

@app.route('/video_feed')
@login_required
def video_feed():
    attendance_type = session.get('attendance_type', 'check_in')

    if 'DETECTED_NAME' in app.config:
        del app.config['DETECTED_NAME']

    return Response(generate_frames(attendance_type), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/process_detection')
@login_required
def process_detection():
    if session.get('face_detected'):
        name = session.get('detected_name')
        attendance_type = session.get('attendance_type', 'check_in')

        attendance_message = mark_attendance_record(name, attendance_type)
        session['attendance_message'] = attendance_message
        session['attendance_success'] = 'success' if 'successful' in attendance_message.lower() else 'error'

        session.pop('face_detected', None)
        session.pop('detected_name', None)
    
    return redirect(url_for('dashboard'))
 
@app.route('/mark_attendance', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    if request.method == 'POST':
        attendance_type = request.form.get('attendance_type', 'check_in')
        session['attendance_type'] = attendance_type
    return render_template('mark_attendance.html', attendance_type=session.get('attendance_type','check_in'))


@app.route('/close_camera')
@login_required
def close_camera():
    global camera
    if camera and camera.isOpened():
        camera.release()
    camera = None
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully!")
    app.run(debug=True)