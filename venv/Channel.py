from typing import Any, Collection, Dict, List, Optional, Sequence, Set


class Channel:
    def __init__(self, server: "Server", name: bytes) -> None:
        self.server = server
        self.name = name
        self.members: Set["Client"] = set()
        self._topic = b""
        self._key: Optional[bytes] = None
        self._state_path: Optional[str]
        if self.server.state_dir:
            fs_safe_name = (
                name.decode(errors="ignore")
                    .replace("_", "__")
                    .replace("/", "_")
            )
            self._state_path = f"{self.server.state_dir}/{fs_safe_name}"
            self._read_state()
        else:
            self._state_path = None

    def add_member(self, client: "Client") -> None:
        self.members.add(client)
