import json
import socket
from collections import defaultdict
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QMainWindow, QLabel, QWidget, QHBoxLayout, QVBoxLayout, QTextEdit, QLineEdit, QPushButton
from Udp_Helper import UDP_Helper
import sounddevice as sd


# ---> NEW: תהליכון שמאזין להודעות צ'אט נכנסות <---
class ChatReceiverThread(QThread):
    message_received = pyqtSignal(str, str)

    def __init__(self, tcp_sock):
        super().__init__()
        self.tcp_sock = tcp_sock
        self.running = True

    def run(self):
        buffer = ""
        self.tcp_sock.settimeout(1.0)
        while self.running:
            try:
                data = self.tcp_sock.recv(1024).decode()
                if not data:
                    continue
                buffer += data
                while "\n" in buffer:
                    msg_str, buffer = buffer.split("\n", 1)
                    if not msg_str.strip(): continue
                    msg = json.loads(msg_str)
                    if msg.get("action") == "chat":
                        sender = msg["data"].get("sender", "Unknown")
                        text = msg["data"].get("message", "")
                        self.message_received.emit(sender, text)
            except socket.timeout:
                continue
            except Exception as e:
                pass

    def stop(self):
        self.running = False
        self.wait()


class ReceiveVideoThread(QThread):
    frame_ready = pyqtSignal(QImage)

    def __init__(self, udp_sock):
        super().__init__()
        self.udp_sock = udp_sock
        self.running = True
        self.frame_buffer = defaultdict(list)

    def run(self):
        while self.running:
            frame_data, addr = UDP_Helper.receive_and_reassemble(self.udp_sock, self.frame_buffer)
            if frame_data:
                img = QImage()
                img.loadFromData(frame_data)
                if not img.isNull():
                    self.frame_ready.emit(img)

    def stop(self):
        self.running = False
        self.wait()


class ReceiveAudioThread(QThread):
    def __init__(self, udp_audio_sock):
        super().__init__()
        self.udp_audio_sock = udp_audio_sock
        self.running = True
        self.chunk = 1024

    def run(self):
        with sd.RawOutputStream(samplerate=44100, blocksize=self.chunk, channels=1, dtype='int16') as stream:
            while self.running:
                try:
                    data, addr = self.udp_audio_sock.recvfrom(65535)
                    stream.write(data)
                except Exception as e:
                    pass

    def stop(self):
        self.running = False
        self.wait()


class ClientRoom(QMainWindow):
    def __init__(self, sock):
        super().__init__()
        self.tcp_sock = sock
        self.setWindowTitle("Zoom - Viewer")
        self.resize(1000, 600)

        # ---> NEW: עיצוב המסך המפוצל <---
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # צד שמאל - וידאו
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("background-color: black;")
        main_layout.addWidget(self.label, stretch=3)

        # צד ימין - צ'אט
        chat_layout = QVBoxLayout()
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type a message...")

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_chat_message)
        self.send_btn.setStyleSheet("background-color: #3498db; color: white; padding: 5px;")

        chat_layout.addWidget(self.chat_display)
        chat_layout.addWidget(self.chat_input)
        chat_layout.addWidget(self.send_btn)
        main_layout.addLayout(chat_layout, stretch=1)

        # יצירת חיבורים ווידאו ואודיו
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.udp_sock.bind(("0.0.0.0", 0))
        except Exception as e:
            print(e)

        my_udp_port = self.udp_sock.getsockname()[1]

        self.udp_audio_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_audio_sock.bind(("0.0.0.0", my_udp_port + 1))

        msg = {"action": "download", "data": {"udp_port": my_udp_port}}
        self.tcp_sock.send((json.dumps(msg) + "\n").encode())

        self.recv_thread = ReceiveVideoThread(self.udp_sock)
        self.recv_thread.frame_ready.connect(self.update_image)
        self.recv_thread.start()

        self.recv_audio_thread = ReceiveAudioThread(self.udp_audio_sock)
        self.recv_audio_thread.start()

        # ---> NEW: הפעלת תהליכון הצ'אט <---
        self.chat_thread = ChatReceiverThread(self.tcp_sock)
        self.chat_thread.message_received.connect(self.update_chat_display)
        self.chat_thread.start()

    def update_image(self, qimg: QImage):
        pixmap = QPixmap.fromImage(qimg)
        self.label.setPixmap(pixmap)

    # ---> NEW: פונקציות הצ'אט <---
    def send_chat_message(self):
        text = self.chat_input.text().strip()
        if text:
            msg = {"action": "chat", "data": {"sender": "Viewer", "message": text}}
            try:
                self.tcp_sock.send((json.dumps(msg) + "\n").encode())
                self.chat_input.clear()
            except Exception as e:
                pass

    def update_chat_display(self, sender, text):
        self.chat_display.append(f"<b>{sender}:</b> {text}")

    def closeEvent(self, event):
        self.recv_thread.stop()
        self.recv_audio_thread.stop()
        self.chat_thread.stop()
        event.accept()