import json
import socket
import sys
from threading import Thread
from tkinter import Image

import cv2

from PyQt6.QtCore import QThread, pyqtSignal, Qt, QByteArray, QBuffer, QIODevice
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


class ClientRoom(QMainWindow):
    def __init__(self,sock):
        self.tcp_sock = sock
        super().__init__()

        self.setWindowTitle("Webcam Live Feed")
        self.resize(800, 600)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self.label)


        msg = {
            "action": "download",
            "data": {},
        }
        self.tcp_sock.send(json.dumps(msg).encode())

        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.bind(("127.0.0.1", 5557))
        Thread(target=self.handle_receive_video,args=(udp_sock,)).start()

    def handle_receive_video(self, udp_sock):
        print("receiving video")
        recv_data = udp_sock.recv(1024)
        img = QImage()
        img.loadFromData(recv_data)
        if img.isNull():
            print("Invalid image")
        else:
            print("Image received:", img.size())
        pixmap = QPixmap.fromImage(img)
        self.label.setPixmap(pixmap)