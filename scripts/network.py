import socket
from types import SimpleNamespace

from .protocol import receive_message, send_message


class Network:
    def __init__(self, app, ip=None, port=5555):
        server = ip or app.config["server"]["ip"]
        self.client = socket.create_connection((server, port), timeout=5)
        try:
            self.client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.player = receive_message(self.client)["player"]
        except Exception:
            self.close()
            raise

    def send(self, direction=None, ready=False):
        send_message(self.client, {"type": "input", "direction": direction, "ready": ready})
        return SimpleNamespace(**receive_message(self.client))

    def close(self):
        self.client.close()
