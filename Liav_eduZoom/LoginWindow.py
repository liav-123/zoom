import hashlib
import json
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QCursor
from PyQt6.QtCore import Qt


class LoginWindow(QMainWindow):
    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        self.setWindowTitle("Zoom - Login")
        self.setFixedSize(400, 500)  # גודל פרופורציונלי למסך התחברות

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # כותרות
        header_label = QLabel("Zoom")
        header_label.setObjectName("header")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subheader_label = QLabel("Log In to your account")
        subheader_label.setObjectName("subheader")
        subheader_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # שדות טקסט
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Username")

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Password")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)  # הסתרת סיסמה כברירת מחדל

        # שורת הסיסמה (שדה + כפתור חשיפה)
        pwd_layout = QHBoxLayout()
        pwd_layout.setSpacing(0)

        self.toggle_pwd_btn = QPushButton("👁️")
        self.toggle_pwd_btn.setObjectName("toggle_btn")
        self.toggle_pwd_btn.setFixedSize(40, 40)
        self.toggle_pwd_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_pwd_btn.clicked.connect(self.toggle_password_visibility)

        pwd_layout.addWidget(self.password_edit)
        pwd_layout.addWidget(self.toggle_pwd_btn)

        # כפתורים
        login_button = QPushButton("Login")
        login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        login_button.clicked.connect(self.handle_login)

        signup_button = QPushButton("Sign Up")
        signup_button.setCursor(Qt.CursorShape.PointingHandCursor)
        signup_button.setStyleSheet("background-color: #2ecc71;")  # צבע ירוק לכפתור הרשמה
        signup_button.clicked.connect(self.handle_signup)

        # הוספת האלמנטים למסך
        main_layout.addWidget(header_label)
        main_layout.addWidget(subheader_label)
        main_layout.addSpacing(20)
        main_layout.addWidget(QLabel("Username:"))
        main_layout.addWidget(self.username_edit)
        main_layout.addWidget(QLabel("Password:"))
        main_layout.addLayout(pwd_layout)
        main_layout.addSpacing(20)
        main_layout.addWidget(login_button)
        main_layout.addWidget(signup_button)
        main_layout.addStretch()

        main_widget.setLayout(main_layout)

        # עיצוב מודרני CSS
        self.setStyleSheet("""
            QWidget {
                background-color: #f4f6f8;
                font-family: Arial;
            }
            QLabel {
                font-size: 14px;
                color: #2c3e50;
                font-weight: bold;
            }
            QLabel#header {
                font-size: 36px;
                font-weight: bold;
                color: #3498db;
            }
            QLabel#subheader {
                font-size: 16px;
                color: #7f8c8d;
                font-weight: normal;
            }
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 15px;
                font-weight: bold;
                border-radius: 5px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton#toggle_btn {
                background-color: transparent;
                color: black;
                padding: 0;
            }
            QPushButton#toggle_btn:hover {
                background-color: #ecf0f1;
            }
        """)

    def toggle_password_visibility(self):
        # מחליף בין מצב הסתרה למצב טקסט רגיל
        if self.password_edit.echoMode() == QLineEdit.EchoMode.Password:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_pwd_btn.setText("🙈")
        else:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_pwd_btn.setText("👁️")

    def handle_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()

        if not username or not password:
            return

        hash_password = hashlib.sha256(password.encode()).hexdigest()
        msg = {
            "action": "login",
            "data": {"username": username, "password": hash_password},
        }

        self.sock.send((json.dumps(msg) + "\n").encode())
        response = self.sock.recv(1024).decode()
        response = json.loads(response)
        self.handle_server_response(response)

    def handle_signup(self):
        from SignupWindow import signupWindow
        self.signup_window = signupWindow(self.sock)
        self.signup_window.show()
        self.close()

    def open_main_window(self, username):
        from LobbyWindow import LobbyWindow
        self.main_window = LobbyWindow(username, self.sock)
        self.main_window.show()
        self.close()

    def handle_server_response(self, response):
        if response["status"] == "success":
            self.open_main_window(response["username"])
        else:
            QMessageBox.warning(self, "Error", "Login failed! Please check your credentials.")