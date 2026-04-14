import json
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont


class LoginWindow(QMainWindow):
    def __init__(self,sock):
        super().__init__()
        self.sock = sock
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.setGeometry(100, 100, 600, 600)
        self.setWindowTitle("Login")

        main_layout = QVBoxLayout()

        header_label = QLabel("Zoom")
        header_label.setFont(QFont("Times", 10, QFont.Weight.Bold))

        subheader_label = QLabel("Log In")
        subheader_label.setFont(QFont("Times", 8, QFont.Weight.Bold))

        username_label = QLabel("Username")
        password_label = QLabel("Password")

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Username")

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Password")

        login_button = QPushButton("Login")
        login_button.clicked.connect(self.handle_login)

        signup_button = QPushButton("Sign Up")
        signup_button.clicked.connect(self.handle_signup)

        main_layout.addWidget(header_label)
        main_layout.addWidget(subheader_label)
        main_layout.addWidget(username_label)
        main_layout.addWidget(self.username_edit)
        main_layout.addWidget(password_label)
        main_layout.addWidget(self.password_edit)
        main_layout.addWidget(login_button)
        main_layout.addWidget(signup_button)

        main_widget.setLayout(main_layout)

    def handle_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()

        if not username or not password:
            return

        msg = {
            "action": "login",
            "data": {"username": username, "password": password},
        }

        # send to server
        self.sock.send((json.dumps(msg) + "\n").encode())
        # receive response from server
        response = self.sock.recv(1024).decode()
        response = json.loads(response)

        # handle response
        self.handle_server_response(response)

    def handle_signup(self):
        print("showing signup window")
        from SignupWindow import signupWindow
        self.signup_window = signupWindow(self.sock)
        self.signup_window.show()
        self.close()

    def open_main_window(self, username):
        from LobbyWindow import LobbyWindow
        print("opening main window")
        self.main_window = LobbyWindow(username,self.sock)
        self.main_window.show()
        self.close()

    def handle_server_response(self, response):
        # response זה dict אחרי json.loads
        if response["status"] == "success":
            self.open_main_window(response["username"])
        else:
            QMessageBox.warning(self, "Error", "Login failed")