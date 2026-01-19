import socket
import sys
from PyQt6.QtWidgets import *
from LoginWindow import LoginWindow

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 5555))
app = QApplication(sys.argv)

login_window = LoginWindow(sock)
login_window.show()
print("created login window")
app.exec()