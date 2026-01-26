import json
import socket
import threading

from DB import DB


class Server:
    def __init__(self):
        self.db = DB()

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('127.0.0.1', 5555))
        self.server.listen(5)
        print("Server Listening on port 5555")

    def run(self):
        while True:
            client, _ = self.server.accept()
            print("Client connected")
            threading.Thread(target=self.handle_client, daemon=True, args=(client,)).start()

    def handle_client(self, client):
        while True:
            msg = client.recv(1024)
            msg = json.loads(msg.decode())
            action = msg['action']
            data = msg['data']
            if action == 'login':
                print(f"login: {data}")
                if self.db.validate_user(data['username'], data['password']):
                    msg = {
                        "status": "success",
                        "username": data["username"]
                    }
                else:
                    msg = {
                        "status": "failed"
                    }
                client.send(json.dumps(msg).encode())

            elif action == 'signup':
                print(f"signup: {data}")
                self.db.add_user(data['username'], data['password'])

            elif action == 'create_room':
                self.room = Room(data["settings"])
                print("room created")
            elif action == 'upload':
                print("starting video upload")
                udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.room.users.append(client.getsockname())
                udp_sock.bind(("127.0.0.1",5556))
                threading.Thread(target=self.handle_upload, daemon=True, args=(udp_sock,)).start()
            elif action == 'download':
                udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.room.users.append((client.getsockname(),udp_sock))



    def handle_upload(self, udp_sock):
        while True:
            bits = udp_sock.recvfrom(1400)
            print("data received")
            for user,udp in self.room.users:
                if user != udp_sock.getsockname():
                    print("sending video")
                    udp.sendto(bits,("127.0.0.1",5557))





class Room:
    def __init__(self,settings):
        self.settings = settings
        self.users = []



server = Server()
server.run()