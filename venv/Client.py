import socket
from typing import Dict
import Channel

Socket = socket.socket


class Client:
    # https://github.com/jrosdahl/miniircd/blob/master/miniircd line 114
    def __init__(self, server: "Server", socket: Socket):
        self.server = server
        self.socket = socket
        self.channels: Dict[bytes, Channel] = {}
        self.username = "Joe"
        if self.server.ipv6:
            host, port = socket.getpeername()

    def sendMessage(self, message):
        pass
