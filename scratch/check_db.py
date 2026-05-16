import sqlite3
try:
    conn = sqlite3.connect('nyx.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, profile_setup_complete FROM user")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()
except Exception as e:
    print(e)
