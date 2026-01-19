import json
import socket
import sys
import cv2

from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel


class VideoThread(QThread):
    frame_ready = pyqtSignal(QImage)

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("Error: Could not open webcam.")
            return

        while self.running:
            ret, frame = cap.read()
            if not ret:
                break

            # OpenCV uses BGR, Qt uses RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            h, w, ch = frame.shape
            bytes_per_line = ch * w

            qimg = QImage(
                frame.data,
                w,
                h,
                bytes_per_line,
                QImage.Format.Format_RGB888
            )

            self.frame_ready.emit(qimg)

        cap.release()

    def stop(self):
        self.running = False
        self.wait()


class HostRoom(QMainWindow):
    def __init__(self,sock,room_settings):
        self.tcp_sock = sock
        self.room_settings = room_settings
        super().__init__()

        self.setWindowTitle("Webcam Live Feed")
        self.resize(800, 600)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self.label)

        self.video_thread = VideoThread()
        self.video_thread.frame_ready.connect(self.update_image)
        self.video_thread.start()
        msg = {
            "action": "upload",
            "data": {},
        }
        self.tcp_sock.send(json.dumps(msg).encode())

        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    def update_image(self, qimg: QImage):
        pixmap = QPixmap.fromImage(qimg)
        qimg.
        self.udp_sock.sendto("".encode(), ('127.0.0.1', 5556))
        self.label.setPixmap(pixmap)

    def closeEvent(self, event):
        self.video_thread.stop()
        event.accept()

