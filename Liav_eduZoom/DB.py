import sqlite3
class DB:
    def __init__(self):
        self.conn = sqlite3.connect('zoom.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users(id INT(255), username TEXT, password TEXT)''')
        self.cursor.close()

    def add_user(self, username, password):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO users(username, password) VALUES(?, ?)''', (username, password))
        print(f"user {username} and password {password} added to users table")
        cursor.close()
        self.conn.commit()

    def validate_user(self, username, password):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT COUNT(username) FROM users WHERE username = ? AND password = ?''', (username,password))
        if cursor.fetchone()[0] == 0:
            cursor.close()
            self.conn.commit()
            return False
        else:
            cursor.close()
            self.conn.commit()
            return True

if __name__ == '__main__':
    db = DB()
    db.add_user("admin", "1234")