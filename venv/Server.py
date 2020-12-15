import ipaddress
import socket
import string
from typing import Dict
from Channel import Channel
import Client
import hashlib
import select

# import irc

Socket = socket.socket


class Server:
    # https://github.com/jrosdahl/miniircd/blob/master/miniircd line 789
    def __init__(self, ports=[1234], password="", channel="test", ipv6=ipaddress.ip_address('::1')) -> None:
        self.ports = ports
        self.ipv6 = ipv6
        self.socketList = []
        self.serverSocket = Socket(socket.AF_INET, socket.SOCK_STREAM)

        # self.listen = listen
        # self.serverSocket.listen()

        # this means that you can reuse addresses for reconnection
        # self.serverSocket.setsockopt((Socket.SOL_SOCKET, Socket.SO_REUSEADDR, 1))

        """
        if not password:
            self.password = hashlib.sha224(b"password").hexdigest()
        else:
            self.password = password
   
        if self.ipv6:
            self.address = socket.getaddrinfo(listen, None, proto=self.serverSocket.IPPROTO_TCP)
        else:
            self.ipv6 = "[::1]"
            server_name_limit = 63  # This is from RFC.
            self.name = socket.getfqdn()[:server_name_limit].encode()
            print("Socket = " + socket.getfqdn())
        """

        self.socketList = [self.serverSocket]
        self.channels: Dict[bytes, Channel] = {}  # key: irc_lower(channelname)
        self.clients: Dict[Socket, Client] = {}
        self.nicknames: Dict[bytes, Client] = {}  # key: irc_lower(nickname)
        # self.threads: Dict[bytes, Channel] = {}

        self.initialiseServer()

    def addChannel(self, name="test") -> Channel:
        channel = Channel(self, name, self.serverSocket)
        newThread = channel.threadID
        name = "#" + name  # RCD channel names have to start with a hashtag
        self.channels = {name: channel}
        return channel

    def initialiseServer(self):
        channel1 = self.addChannel("test")
        channel1.refreshChannel()
        for port in self.ports:
            s = socket.socket(
                socket.AF_INET6 if self.ipv6 else socket.AF_INET,
                socket.SOCK_STREAM,
            )
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.ipv6, port))
            s.listen(5)
            self.socketList.append(s)

        """
        self.serverSocket.bind((Socket, bytes(self.ports[0])))
        self.serverSocket.listen()
        """

    def removeClient(self):
        pass

    def addClient(self, channel: Channel, client: Client):
        Channel.addMember(client)
