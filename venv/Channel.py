from typing import Any, Collection, Dict, List, Optional, Sequence, Set
import Server


class Channel:
    def __init__(self, server: "Server", name: bytes) -> None:
        self.server = server
        self.name = name
        self.members: Set["Client"] = set()

    def add_member(self, client: "Client") -> None:
        self.members.add(client)
