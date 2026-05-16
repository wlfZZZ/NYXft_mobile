from app import app, db, User

with app.app_context():
    # Update all users to PIN 7829 for the user
    users = User.query.all()
    for user in users:
        user.quick_pin = "7829"
        print(f"PROTOCOL: Reset PIN for {user.email} to 7829")
    db.session.commit()
    print("SUCCESS: Vault access synchronized.")
