# create_admin.py
from app import create_app
from models import db, Admin

app = create_app()

with app.app_context():
    db.create_all()
    
    admin=Admin.query.filter_by(username='admin').first()
    if not admin:
        admin = Admin(username='admin')
        admin.setPassword('admin@_17')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created successfully!")
    else:
        print("⚠️ Admin user already exists.")