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
    def __init__(self, ports=None, password="", channel="test", ipv6=ipaddress.ip_address('::1')) -> None:
        if ports is None:
            ports = [1234]  # default port for server

        self.ports = ports
        self.ipv6 = ipv6
        self.socketList = []
        self.serverSocket = Socket(family=socket.AF_INET6)

        # self.listen = listen
        # self.serverSocket.listen()

        # this means that you can reuse addresses for reconnection
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

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
        self.channels: Dict[string, Channel] = {}  # key: irc_lower(channelname)
        self.clients: Dict[Socket, Client] = {}
        self.nicknames: Dict[bytes, Client] = {}  # key: irc_lower(nickname)
        # self.threads: Dict[bytes, Channel] = {}

        self.initialiseServer()

    def addChannel(self, name="test") -> Channel:
        name = "#" + name  # RCD channel names have to start with a hashtag
        name = name[0:63]
        channel = Channel(self, name, self.serverSocket)
        self.serverSocket.listen()
        # newThread = channel.threadID
        self.channels[name] = channel
        return channel

    def initialiseServer(self):
        # address = socket.getaddrinfo(str(self.ipv6), self.ports[0], proto=socket.IPPROTO_TCP)[0][4][0]
        # address = [addr for addr in socket.getaddrinfo(self.ipv6, None) if socket.AF_INET6 == addr[0]]
        ipv4 = '127.0.0.1'

        self.serverSocket.bind((str(self.ipv6), self.ports[0]))
        self.serverSocket.listen()

        print(f'Listening for connections on {self.ipv6}:{self.ports[0]}...')

        channel1 = self.addChannel()
        channel1.refreshChannel()
        """
        for port in self.ports:
            s = socket.socket(
                socket.AF_INET6 if self.ipv6 else socket.AF_INET,
                socket.SOCK_STREAM,
            )
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.ipv6, port))
            s.listen(5)
            self.socketList.append(s)


        self.serverSocket.bind((Socket, bytes(self.ports[0])))
        self.serverSocket.listen()
        """

    def removeClient(self):
        pass

    def addClient(self, channel: Channel, client: Client):
        Channel.addMember(client)
