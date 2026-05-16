import os
from app import db, app

# Destruct old schema
if os.path.exists('nyx.db'):
    try:
        os.remove('nyx.db')
        print("OLD DATABASE PURGED.")
    except Exception as e:
        print(f"ERROR: Database is locked. Close all terminal windows and try again. {e}")

# Rebuild high-fidelity schema
with app.app_context():
    db.create_all()
    print("NEW SCHEMA DEPLOYED SUCCESSFULLY.")
