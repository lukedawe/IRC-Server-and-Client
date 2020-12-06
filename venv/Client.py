import re
import socket
from typing import Dict
import Channel

Socket = socket.socket

class Client:
    def __init__(self, server: "Server", socket: Socket) -> None:
        self.server = server
        self.socket = socket
        self.channels: Dict[bytes, Channel] = {}
        self.user = b""
        if self.server.ipv6:
            host, port, _, _ = socket.getpeername()
        else:
            host, port = socket.getpeername()
