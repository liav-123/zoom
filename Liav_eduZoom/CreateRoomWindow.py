import json

from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from Liav_eduZoom.HostRoom import HostRoom


class CreateRoomWindow(QWidget):
    def __init__(self,sock):
        super().__init__()
        self.sock = sock
        self.setWindowTitle("Create Room")
        self.setFixedSize(500, 500)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        # כותרת
        title = QLabel("Create Room")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # טופס
        form = QFormLayout()
        form.setSpacing(15)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        # Limit people
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(2, 100)
        self.limit_spin.setValue(10)

        # Mic
        self.mic_combo = QComboBox()
        self.mic_combo.addItems(["On", "Off"])

        # Share screen
        self.screen_combo = QComboBox()
        self.screen_combo.addItems(["Everyone", "Host Only"])

        # Join before host
        self.join_checkbox = QCheckBox("Allow")

        form.addRow("Limit People:", self.limit_spin)
        form.addRow("Microphone:", self.mic_combo)
        form.addRow("Share Screen:", self.screen_combo)
        form.addRow("Join Before Host:", self.join_checkbox)

        # Host only section
        host_group = QGroupBox("Host Only Settings")
        host_layout = QVBoxLayout()

        self.mute_cb = QCheckBox("Mute participants on join")
        self.lock_cb = QCheckBox("Lock room")
        self.chat_cb = QCheckBox("Disable chat")

        host_layout.addWidget(self.mute_cb)
        host_layout.addWidget(self.lock_cb)
        host_layout.addWidget(self.chat_cb)
        host_group.setLayout(host_layout)

        # Create button
        create_btn = QPushButton("Create Room")
        create_btn.setFixedHeight(55)
        create_btn.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.clicked.connect(self.handle_create_room)

        # עיצוב
        self.setStyleSheet("""
            QWidget {
                background-color: #f4f6f8;
                font-size: 14px;
            }

            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 10px;
                margin-top: 10px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }

            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 15px;
            }

            QPushButton:hover {
                background-color: #27ae60;
            }
        """)

        main_layout.addWidget(title)
        main_layout.addLayout(form)
        main_layout.addWidget(host_group)
        main_layout.addStretch()
        main_layout.addWidget(create_btn)

        self.setLayout(main_layout)

    def handle_create_room(self):
        limit_people = self.limit_spin.value()
        mic = self.mic_combo.currentText()
        screen = self.screen_combo.currentText()
        join = self.join_checkbox.isChecked()
        mute_before_join = self.mute_cb.isChecked()
        lock_room = self.lock_cb.isChecked()
        disable_chat = self.chat_cb.isChecked()

        room_settings = {
            "limit_people": limit_people,
            "mic": mic,
            "screen": screen,
            "join": join,
            "mute_before_join": mute_before_join,
            "lock_room": lock_room,
            "disable_chat": disable_chat
        }
        msg = {"action": "create_room", "data": {"settings":room_settings}}
        print(room_settings)
        self.sock.send(json.dumps(msg).encode())
        self.host_window = HostRoom(self.sock,room_settings)
        self.host_window.show()
        self.close()