import sqlite3
import os

db_path = 'nyx.db'

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add fiber column if not exists
        try:
            cursor.execute('ALTER TABLE daily_nutrition_log ADD COLUMN fiber FLOAT DEFAULT 0.0')
            print("Added 'fiber' column.")
        except sqlite3.OperationalError:
            print("'fiber' column already exists.")
            
        # Add sugar column if not exists
        try:
            cursor.execute('ALTER TABLE daily_nutrition_log ADD COLUMN sugar FLOAT DEFAULT 0.0')
            print("Added 'sugar' column.")
        except sqlite3.OperationalError:
            print("'sugar' column already exists.")
            
        conn.commit()
        conn.close()
        print("Database migration completed successfully.")
    except Exception as e:
        print(f"Error during migration: {e}")
else:
    print(f"Database file {db_path} not found.")
