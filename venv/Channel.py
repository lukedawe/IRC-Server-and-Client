import threading
from typing import Any, Collection, Dict, List, Optional, Sequence, Set
import Server
from Client import Client

HEADER_LENGTH = 10

class Channel:
    # https://github.com/jrosdahl/miniircd/blob/master/miniircd line 47
    threadID = None

    def __init__(self, server: "Server", name: bytes) -> None:
        self.server = server
        self.name = name
        self.members = []
        self.threadID = threading.get_ident()

    def addMember(self, client) -> None:
        self.members.append(client)

    def removeClient(self, client):
        pass

    def recieveMessage(self, clientSocket):
        try:
            messageHeader = clientSocket.recv(HEADER_LENGTH)

            if not len(messageHeader):
                return False

            messageLength = int(messageHeader.decode('utf-8').strip())
            return {'header': messageHeader, 'data': clientSocket.recv(messageLength)}

        except:
            return False
