import json
import socket
import threading
from collections import defaultdict
from DB import DB

class Server:
    def __init__(self):
        self.db = DB()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('127.0.0.1', 5555))
        self.server.listen(5)
        print("Server Listening on port 5555")

        # Video UDP socket
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.bind(("127.0.0.1", 5556))

        # Audio UDP socket
        self.udp_audio_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_audio_sock.bind(("127.0.0.1", 5557))

        self.room = Room({})

        threading.Thread(target=self.handle_upload, daemon=True).start()
        threading.Thread(target=self.handle_audio_upload, daemon=True).start()

    def handle_audio_upload(self):
        print("Starting audio relay service")
        while True:
            try:
                packet, addr = self.udp_audio_sock.recvfrom(65535)
                for viewer_addr in self.room.viewers:
                    audio_viewer_addr = (viewer_addr[0], viewer_addr[1] + 1)
                    self.udp_audio_sock.sendto(packet, audio_viewer_addr)
            except Exception as e:
                pass

    def handle_upload(self):
        print("Starting video chunk relay service")
        while True:
            try:
                packet, addr = self.udp_sock.recvfrom(65535)
                for viewer_addr in self.room.viewers:
                    self.udp_sock.sendto(packet, viewer_addr)
            except Exception as e:
                pass

    def run(self):
        while True:
            client, addr = self.server.accept()
            print(f"Client connected: {addr}")
            threading.Thread(target=self.handle_client, daemon=True, args=(client,)).start()

    def handle_client(self, client):
        buffer = ""
        while True:
            try:
                data = client.recv(1024).decode()
                if not data:
                    break
                buffer += data

                while "\n" in buffer:
                    msg_str, buffer = buffer.split("\n", 1)
                    if not msg_str.strip(): continue

                    msg = json.loads(msg_str)
                    action = msg['action']
                    data_payload = msg['data']

                    if action == 'login':
                        if self.db.validate_user(data_payload['username'], data_payload['password']):
                            resp = {"status": "success", "username": data_payload["username"]}
                        else:
                            resp = {"status": "failed"}
                        client.send((json.dumps(resp) + "\n").encode())

                    elif action == 'signup':
                        self.db.add_user(data_payload['username'], data_payload['password'])
                        client.send((json.dumps({"status": "success"}) + "\n").encode())

                    elif action == 'create_room':
                        self.room = Room(data_payload["settings"])
                        self.room.host_ip = client.getpeername()[0]
                        self.room.tcp_clients.append(client) # שמירת חיבור ה-TCP של המארח
                        print("Room created")

                    elif action == 'upload':
                        print("Host registered for upload")

                    elif action == 'download':
                        client_ip = client.getpeername()[0]
                        client_port = data_payload["udp_port"]
                        self.room.viewers.append((client_ip, client_port))
                        self.room.tcp_clients.append(client) # שמירת חיבור ה-TCP של הצופה
                        print(f"Added viewer {client_ip}:{client_port}")

                    # ---> NEW: ניתוב הודעות הצ'אט <---
                    elif action == 'chat':
                        for c in self.room.tcp_clients:
                            try:
                                c.send((json.dumps(msg) + "\n").encode())
                            except Exception as e:
                                pass

            except Exception as e:
                print("Client disconnected or error:", e)
                if client in self.room.tcp_clients:
                    self.room.tcp_clients.remove(client)
                break
        client.close()

class Room:
    def __init__(self, settings):
        self.settings = settings
        self.host_ip = None
        self.viewers = []
        self.tcp_clients = [] # רשימה חדשה ששומרת את כל חיבורי ה-TCP לטובת הצ'אט

if __name__ == "__main__":
    server = Server()
    server.run()