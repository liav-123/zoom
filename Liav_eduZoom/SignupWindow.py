import hashlib
import json
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QCursor
from PyQt6.QtCore import Qt


class signupWindow(QWidget):
    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        self.setWindowTitle("Zoom - Sign Up")
        self.setFixedSize(400, 500)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # כותרות
        header_label = QLabel("Sign Up")
        header_label.setObjectName("header")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subheader_label = QLabel("Create a new user")
        subheader_label.setObjectName("subheader")
        subheader_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # שדות
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Username")

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Password")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        # שורת סיסמה עם חשיפה
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
        continue_button = QPushButton("Create Account")
        continue_button.setCursor(Qt.CursorShape.PointingHandCursor)
        continue_button.setStyleSheet("background-color: #2ecc71;")
        continue_button.clicked.connect(self.handle_signup)

        back_button = QPushButton("Back to Login")
        back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        back_button.clicked.connect(self.go_back_to_login)

        main_layout.addWidget(header_label)
        main_layout.addWidget(subheader_label)
        main_layout.addSpacing(20)
        main_layout.addWidget(QLabel("Username:"))
        main_layout.addWidget(self.username_edit)
        main_layout.addWidget(QLabel("Password:"))
        main_layout.addLayout(pwd_layout)
        main_layout.addSpacing(20)
        main_layout.addWidget(continue_button)
        main_layout.addWidget(back_button)
        main_layout.addStretch()

        self.setLayout(main_layout)

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
                color: #2ecc71;
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
                border: 2px solid #2ecc71;
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
        if self.password_edit.echoMode() == QLineEdit.EchoMode.Password:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_pwd_btn.setText("🙈")
        else:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_pwd_btn.setText("👁️")

    def go_back_to_login(self):
        from LoginWindow import LoginWindow
        self.login_window = LoginWindow(self.sock)
        self.login_window.show()
        self.close()

    def handle_signup(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()

        if username == '' or password == '':
            return

        hash_password = hashlib.sha256(password.encode()).hexdigest()
        msg = {
            "action": "signup",
            "data": {"username": username, "password": hash_password},
        }
        self.sock.send((json.dumps(msg) + "\n").encode())

        # ожидание תשובה מהשרת
        response_data = self.sock.recv(1024).decode().strip()
        if response_data:
            response = json.loads(response_data)
            if response.get("status") == "success":
                self.go_back_to_login()