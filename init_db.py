import sqlite3
import bcrypt

# Connect
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Create table
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
)
''')

# Insert an example admin user
password = 'admin123'  # You can change this
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', ('admin', hashed))
conn.commit()
conn.close()

print("Database initialized with default admin user.")
