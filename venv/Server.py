import ipaddress
import socket
from typing import Dict
from Channel import Channel
import Client
import hashlib
import irc

Socket = socket.socket


class Server:
    # https://github.com/jrosdahl/miniircd/blob/master/miniircd line 789
    def __init__(self, ports=[], password="", channel="test", ipv6=ipaddress.ip_address('::1'),
                 listen=6667) -> None:
        self.ports = ports
        self.ipv6 = ipv6

        if not password:
            self.password = hashlib.sha224(b"password").hexdigest()
        else:
            self.password = password

        if self.ipv6:
            self.address = socket.getaddrinfo(listen, None, proto=socket.IPPROTO_TCP)
        else:
            server_name_limit = 63  # From the RFC.
            self.name = socket.getfqdn()[:server_name_limit].encode()
            print("Socket = " + socket.getfqdn())

        self.channels: Dict[bytes, Channel] = {}  # key: irc_lower(channelname)
        self.clients: Dict[Socket, Client] = {}
        self.nicknames: Dict[bytes, Client] = {}  # key: irc_lower(nickname)

    def addChannel(self, name):
        channel = Channel()
        newThread = channel.threadID
        self.channels = {name: channel}

    def initialiseServer(self):
        self.addChannel("test")
