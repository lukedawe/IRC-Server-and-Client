import ipaddress
import socket
from typing import Dict
from Channel import Channel
import Client
import hashlib
import select
import irc

Socket = socket.socket
HEADER_LENGTH = 10


class Server:
    # https://github.com/jrosdahl/miniircd/blob/master/miniircd line 789
    def __init__(self, ports=[], password="", channel="test", ipv6=ipaddress.ip_address('::1'),
                 listen=6667) -> None:
        self.ports = ports
        self.ipv6 = ipv6
        self.serverSocket = Socket
        # self.serverSocket.listen()

        # this means that you can reuse addresses for reconnection
        self.serverSocket.setsockopt((self.serverSocket.SOL_SOCKET, self.Socket.SO_REUSEADDR, 1))
        self.serverSocket.bind(self.ipv6, self.ports)

        if not password:
            self.password = hashlib.sha224(b"password").hexdigest()
        else:
            self.password = password

        if self.ipv6:
            self.address = self.serverSocket.getaddrinfo(listen, None, proto=self.serverSocket.IPPROTO_TCP)
        else:
            self.ipv6 = "[::1]"
            server_name_limit = 63  # This is from RFC.
            self.name = self.serverSocket.getfqdn()[:server_name_limit].encode()
            print("Socket = " + socket.getfqdn())

        self.channels: Dict[bytes, Channel] = {}  # key: irc_lower(channelname)
        self.client: Dict[Socket, Client] = {}
        self.nicknames: Dict[bytes, Client] = {}  # key: irc_lower(nickname)
        self.threads: Dict[bytes, Channel] = {}

        self.initialiseServer()

    def addChannel(self, name="test") -> None:
        channel = Channel
        newThread = channel.threadID
        self.channels = {name: channel}

    def initialiseServer(self):
        self.addChannel("test")

    def removeClient(self):
        pass

    def distributeMessage(self):
        pass
