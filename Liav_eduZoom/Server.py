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

        # Bind ONE central UDP socket for relaying video chunks
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.bind(("127.0.0.1", 5556))

        self.room = Room({})  # Supporting one global room for now

        # Start the video relay service
        threading.Thread(target=self.handle_upload, daemon=True).start()

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

                # Process complete JSON messages separated by newline
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
                        print("Room created")

                    elif action == 'upload':
                        print("Host registered for upload")

                    elif action == 'download':
                        # Client tells us which dynamic UDP port it is listening on
                        client_ip = client.getpeername()[0]
                        client_port = data_payload["udp_port"]
                        self.room.viewers.append((client_ip, client_port))
                        print(f"Added viewer {client_ip}:{client_port}")

            except Exception as e:
                print("Client disconnected or error:", e)
                break
        client.close()

    def handle_upload(self):
        print("Starting video chunk relay service")
        while True:
            try:
                # Receive a chunk from the host
                packet, addr = self.udp_sock.recvfrom(65535)
                # Forward the chunk exactly as-is to all viewers
                for viewer_addr in self.room.viewers:
                    self.udp_sock.sendto(packet, viewer_addr)
            except Exception as e:
                print("Error relaying video:", e)


class Room:
    def __init__(self, settings):
        self.settings = settings
        self.host_ip = None
        self.viewers = []


if __name__ == "__main__":
    server = Server()
    server.run()