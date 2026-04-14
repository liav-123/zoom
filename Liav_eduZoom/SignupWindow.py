import json
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont


class signupWindow(QWidget):
    def __init__(self,sock):
        super().__init__()
        self.sock = sock
        self.setGeometry(100, 100, 600, 600)
        self.setWindowTitle("Signup")

        main_layout = QVBoxLayout()

        header_label = QLabel("Signup")
        header_label.setFont(QFont("Times", 10, QFont.Weight.Bold))

        subheader_label = QLabel("Crate a user")
        subheader_label.setFont(QFont("Times", 8, QFont.Weight.Bold))

        username_label = QLabel("Username")
        password_label = QLabel("Password")

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Username")

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Password")

        login_button = QPushButton("continue")
        login_button.clicked.connect(self.handle_signup)

        main_layout.addWidget(header_label)
        main_layout.addWidget(subheader_label)
        main_layout.addWidget(username_label)
        main_layout.addWidget(self.username_edit)
        main_layout.addWidget(password_label)
        main_layout.addWidget(self.password_edit)
        main_layout.addWidget(login_button)

        self.setLayout(main_layout)

    def handle_signup(self):
        from LoginWindow import LoginWindow
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        if username == '' or password == '':
            return
        else:
            msg = {
                "action": "signup",
                "data": {"username": username, "password": password},
            }
            self.sock.send((json.dumps(msg) + "\n").encode())
            # Wait for server success response
            response_data = self.sock.recv(1024).decode().strip()
            if response_data:
                response = json.loads(response_data)
                if response.get("status") == "success":
                    from LoginWindow import LoginWindow
                    self.login_window = LoginWindow(self.sock)
                    self.login_window.show()
                    self.close()