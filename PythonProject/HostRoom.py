import json
import socket
import time
import cv2
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QByteArray, QBuffer, QIODevice
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QMainWindow, QLabel, QWidget, QHBoxLayout, QVBoxLayout, QTextEdit, QLineEdit, QPushButton
from Udp_Helper import UDP_Helper
import sounddevice as sd



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


class VideoThread(QThread):
    frame_ready = pyqtSignal(QImage)

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        print("starting video thread")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open webcam.")
            return

        while self.running:
            ret, frame = cap.read()
            if not ret: break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w

            # חשוב: .copy() מונע קריסות זיכרון
            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
            self.frame_ready.emit(qimg)
            time.sleep(1 / 30)
        cap.release()

    def stop(self):
        self.running = False
        self.wait()


class AudioSenderThread(QThread):
    def __init__(self, udp_sock, server_addr):
        super().__init__()
        self.udp_sock = udp_sock
        self.server_addr = server_addr
        self.running = True
        self.chunk = 1024

    def run(self):
        print("Starting audio sending thread")
        with sd.RawInputStream(samplerate=44100, blocksize=self.chunk, channels=1, dtype='int16') as stream:
            while self.running:
                try:
                    data, overflowed = stream.read(self.chunk)
                    self.udp_sock.sendto(data, self.server_addr)
                except Exception as e:
                    pass

    def stop(self):
        self.running = False
        self.wait()


class HostRoom(QMainWindow):
    def __init__(self, sock, room_settings):
        super().__init__()
        self.tcp_sock = sock
        self.room_settings = room_settings

        self.setWindowTitle("Zoom - Host")
        self.resize(1000, 600)  # הרחבנו את החלון כדי שיהיה מקום לצ'אט

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
        self.send_btn.setStyleSheet("background-color: #2ecc71; color: white; padding: 5px;")

        chat_layout.addWidget(self.chat_display)
        chat_layout.addWidget(self.chat_input)
        chat_layout.addWidget(self.send_btn)
        main_layout.addLayout(chat_layout, stretch=1)

        # הפעלת תהליכוני הווידאו והאודיו
        msg = {"action": "upload", "data": {}}
        self.tcp_sock.send((json.dumps(msg) + "\n").encode())

        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.video_thread = VideoThread()
        self.video_thread.frame_ready.connect(self.update_image)
        self.video_thread.start()

        self.udp_audio_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.audio_thread = AudioSenderThread(self.udp_audio_sock, ("127.0.0.1", 5557))
        self.audio_thread.start()

        # ---> NEW: הפעלת תהליכון הצ'אט <---
        self.chat_thread = ChatReceiverThread(self.tcp_sock)
        self.chat_thread.message_received.connect(self.update_chat_display)
        self.chat_thread.start()

    frame_counter = 0

    def update_image(self, qimg: QImage):
        pixmap = QPixmap.fromImage(qimg)
        self.label.setPixmap(pixmap)
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        qimg.save(buffer, "JPG")
        buffer.close()
        data = byte_array.data()
        try:
            UDP_Helper.send_frame_to_server(self.udp_sock, data, ("127.0.0.1", 5556), self.frame_counter)
            self.frame_counter = (self.frame_counter + 1) % 256
        except Exception as e:
            pass

    # ---> NEW: פונקציות הצ'אט <---
    def send_chat_message(self):
        text = self.chat_input.text().strip()
        if text:
            msg = {"action": "chat", "data": {"sender": "Host", "message": text}}
            try:
                self.tcp_sock.send((json.dumps(msg) + "\n").encode())
                self.chat_input.clear()  # ניקוי שורת ההקלדה אחרי השליחה
            except Exception as e:
                pass

    def update_chat_display(self, sender, text):
        self.chat_display.append(f"<b>{sender}:</b> {text}")

    def closeEvent(self, event):
        self.video_thread.stop()
        self.audio_thread.stop()
        self.chat_thread.stop()  # עצירת הצ'אט
        event.accept()