import sqlite3
import threading

class DB:
    def __init__(self):
        self.lock = threading.Lock()
        self.conn = sqlite3.connect('zoom.db', check_same_thread=False)
        with self.lock:
            cursor = self.conn.cursor()
            # Changed id to AUTOINCREMENT so it is actually utilized
            cursor.execute('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)''')
            self.conn.commit()

    def add_user(self, username, password):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''INSERT INTO users(username, password) VALUES(?, ?)''', (username, password))
            self.conn.commit()
            print(f"User {username} added to users table")

    def validate_user(self, username, password):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT COUNT(username) FROM users WHERE username = ? AND password = ?''', (username, password))
            return cursor.fetchone()[0] > 0