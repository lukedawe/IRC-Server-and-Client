import threading
from typing import Any, Collection, Dict, List, Optional, Sequence, Set
import Server
from Client import Client


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
