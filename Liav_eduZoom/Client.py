import socket
import sys
from PyQt6.QtWidgets import *
from LoginWindow import LoginWindow
from config import SERVER_IP

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, 5555))
    app = QApplication(sys.argv)
    login_window = LoginWindow(sock)
    login_window.show()
    print("created login window")
    app.exec()

except BaseException as e:
    print(e)
