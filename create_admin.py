# create_admin.py
from dotenv import load_dotenv
from app import create_app
from models import db, Admin
import os

load_dotenv()

app = create_app()

admin_username = os.getenv("ADMIN_USERNAME")
admin_password = os.getenv("ADMIN_PASSWORD")

print("ENV USERNAME:", admin_username)

with app.app_context():
    db.create_all()

    all_admins = Admin.query.all()

    print("All admins:", all_admins)
    
    admin=Admin.query.filter_by(username=admin_username).first()
    
    print("Found admin:", admin)
    
    if not admin:
        admin = Admin(username=admin_username)
        admin.setPassword(admin_password)
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created successfully!")
    else:
        print("⚠️ Admin user already exists.")