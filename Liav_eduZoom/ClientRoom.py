import json
import socket
from collections import defaultdict
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QMainWindow, QLabel
from Udp_Helper import UDP_Helper

class ReceiveVideoThread(QThread):
    frame_ready = pyqtSignal(QImage)

    def __init__(self, udp_sock):
        super().__init__()
        self.udp_sock = udp_sock
        self.running = True
        self.frame_buffer = defaultdict(list)

    def run(self):
        print("Receiving video thread started")
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

class ClientRoom(QMainWindow):
    def __init__(self, sock):
        super().__init__()
        self.tcp_sock = sock
        self.setWindowTitle("Webcam Live Feed - Viewer")
        self.resize(800, 600)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self.label)

        # Bind to a dynamic ephemeral port (0) so multiple clients don't collide
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.bind(("127.0.0.1", 0))
        my_udp_port = self.udp_sock.getsockname()[1]

        # Tell server our port
        msg = {
            "action": "download",
            "data": {"udp_port": my_udp_port},
        }
        self.tcp_sock.send((json.dumps(msg) + "\n").encode())

        # Start QThread for GUI-safe receiving
        self.recv_thread = ReceiveVideoThread(self.udp_sock)
        self.recv_thread.frame_ready.connect(self.update_image)
        self.recv_thread.start()

        # Existing video socket creation
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.bind(("127.0.0.1", 0))
        my_udp_port = self.udp_sock.getsockname()[1]

        # ---> NEW: Audio Socket Creation (Video port + 1) <---
        self.udp_audio_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_audio_sock.bind(("127.0.0.1", my_udp_port + 1))

        # Tell server our port
        msg = {
            "action": "download",
            "data": {"udp_port": my_udp_port},
        }
        self.tcp_sock.send((json.dumps(msg) + "\n").encode())

        # Start QThread for GUI-safe receiving (Video)
        self.recv_thread = ReceiveVideoThread(self.udp_sock)
        self.recv_thread.frame_ready.connect(self.update_image)
        self.recv_thread.start()

        # ---> NEW: Start Audio Thread <---
        self.recv_audio_thread = ReceiveAudioThread(self.udp_audio_sock)
        self.recv_audio_thread.start()

    def update_image(self, qimg: QImage):
        pixmap = QPixmap.fromImage(qimg)
        self.label.setPixmap(pixmap)

    def closeEvent(self, event):
        self.recv_thread.stop()
        self.recv_audio_thread.stop()  # ---> NEW: Stop audio thread <---
        event.accept()


import sounddevice as sd
from PyQt6.QtCore import QThread

class ReceiveAudioThread(QThread):
    def __init__(self, udp_audio_sock):
        super().__init__()
        self.udp_audio_sock = udp_audio_sock
        self.running = True
        self.chunk = 1024

    def run(self):
        print("Receiving audio thread started")
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