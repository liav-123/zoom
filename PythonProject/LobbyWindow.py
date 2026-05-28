import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


class LobbyWindow(QWidget):
    def __init__(self, username,sock):
        super().__init__()

        self.setWindowTitle("Lobby")
        self.setFixedSize(600, 600)
        self.sock = sock
        # Layout ראשי
        main_layout = QVBoxLayout()
        main_layout.setSpacing(40)
        main_layout.setContentsMargins(60, 80, 60, 80)

        # כותרת
        title = QLabel(f"Welcome, {username}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))

        # כפתורים
        create_room_btn = QPushButton("Create Room")
        create_room_btn.clicked.connect(self.hundle_CreateRoomWindow)

        join_room_btn = QPushButton("Join Room")
        join_room_btn.clicked.connect(self.hundle_JoinRoom)

        button_font = QFont("Arial", 20, QFont.Weight.Bold)
        create_room_btn.setFont(button_font)
        join_room_btn.setFont(button_font)

        for btn in (create_room_btn, join_room_btn):
            btn.setFixedHeight(90)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # עיצוב CSS
        self.setStyleSheet("""
            QWidget {
                background-color: #f4f6f8;
            }

            QLabel {
                color: #2c3e50;
            }

            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 20px;
            }

            QPushButton:hover {
                background-color: #2980b9;
            }

            QPushButton:pressed {
                background-color: #1f618d;
            }
        """)

        main_layout.addWidget(title)
        main_layout.addStretch()
        main_layout.addWidget(create_room_btn)
        main_layout.addWidget(join_room_btn)
        main_layout.addStretch()



        self.setLayout(main_layout)

    def hundle_CreateRoomWindow(self):
        print("showing create room window")
        from CreateRoomWindow import CreateWindow
        print("creating createRoomWindow....")
        self.create_Room_Window = CreateWindow(self.sock)
        print("showing createRoomWindow")
        self.create_Room_Window.show()
        print("finished showing createRoomWindow")
        self.hide()

    def hundle_JoinRoom(self):
        print("showing joing room window")
        from ClientRoom import ClientRoom
        self.clientRoom = ClientRoom(self.sock)
        self.clientRoom.show()
        self.close()