import string
import threading
from typing import Any, Collection, Dict, List, Optional, Sequence, Set
# import Server
from Client import Client
import select

HEADER_LENGTH = 10


class Channel:
    # https://github.com/jrosdahl/miniircd/blob/master/miniircd line 47
    threadID = None

    def __init__(self, server: "Server", name: str, serverSocket) -> None:
        self.server = server
        self.name = name
        self.members = {}
        self.threadID = threading.get_ident()
        self.serverSocket = serverSocket
        self.socketList = [serverSocket]
        self.clientList = {}

    def addMember(self, client, clientaddress) -> None:
        self.members[client] = clientaddress

    def removeClient(self, client):
        print('Closed connection from: {}'.format(self.clientList[client]['msgData'].decode('utf-8')))

        # Remove from list for socket.socket()
        self.socketList.remove(client)

        # Remove from our list of users
        del self.clientList[client]

