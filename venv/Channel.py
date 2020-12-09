import threading
from typing import Any, Collection, Dict, List, Optional, Sequence, Set
import Server
from Client import Client


class Channel:
    def __init__(self, server: "Server", name: bytes) -> None:
        self.server = server
        self.name = name
        self.members: Set["Client"] = set()
        self.thread_id = threading.get_ident()

    def add_member(self, client: "Client") -> None:
        self.members.add(client)
