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


server = Server()
server.run()