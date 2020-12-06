import re
import socket
from typing import Dict

Socket = socket.socket
import Channel


class Client:
    def __init__(self, server: "Server", socket: Socket) -> None:
        self.server = server
        self.socket = socket
        self.channels: Dict[bytes, Channel] = {}
