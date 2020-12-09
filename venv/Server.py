import ipaddress
import logging
import os
import re
import select
import socket
import string
import sys
import tempfile
import time
from typing import Dict
from argparse import ArgumentParser
import Channel
import Client
import hashlib

Socket = socket.socket


class Server:
    def __init__(self, ports=6667, password="", channel="test", ipv6=ipaddress.ip_address('2001:db8::'),
                 listen="") -> None:
        self.ports = ports
        self.ipv6 = ipv6

        if not password:
            self.password = hashlib.sha224(b"password").hexdigest()
        else:
            self.password = password

        if self.ipv6:
            self.address = socket.getaddrinfo(listen, None, proto=socket.IPPROTO_TCP)
        elif listen:
            self.address = socket.gethostbyname(listen)
        else:
            self.address = ""
            server_name_limit = 63  # From the RFC.
            self.name = socket.getfqdn(self.address)[:server_name_limit].encode()

        self.channels: Dict[bytes, Channel] = {}  # key: irc_lower(channelname)
        self.clients: Dict[Socket, Client] = {}
