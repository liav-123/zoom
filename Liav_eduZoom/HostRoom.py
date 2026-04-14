import json
import socket


import cv2

from PyQt6.QtCore import QThread, pyqtSignal, Qt, QByteArray, QBuffer, QIODevice
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import  QMainWindow, QLabel
from Udp_Helper import UDP_Helper


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
            print("screen captured")
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
            print("frame emitted")
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
        print("upload action sent to server")

        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("udp socket created")


    frame_counter = 0
    def update_image(self, qimg: QImage):
        print("frame received")
        pixmap = QPixmap.fromImage(qimg)
        self.label.setPixmap(pixmap)
        print("pixmap displayed")
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)

        qimg.save(buffer, "JPG")  # or b"JPG"
        buffer.close()

        data = byte_array.data()
        print(byte_array.size())
        try:
            UDP_Helper.send_frame_to_server(self.udp_sock,data,("127.0.0.1",5556),self.frame_counter)
            self.frame_counter = (self.frame_counter + 1) % 256
        except Exception as e:
            print("error sending data to the server ",e)
        print("frame data sent to server")



    def closeEvent(self, event):
        self.video_thread.stop()
        event.accept()


