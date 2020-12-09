import socket
from typing import Dict
import Channel

Socket = socket.socket

class Client:
    def __init__(self, server: "Server", socket: Socket):
        self.server = server
        self.socket = socket
        self.channels: Dict[bytes, Channel] = {}
        self.username = "Joe"
        if self.server.ipv6:
            host, port = socket.getpeername()

    def sendMessage(self, message):
        pass
