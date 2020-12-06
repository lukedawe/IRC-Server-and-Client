import logging
import os
import re
import select
import socket
import string
import sys
import tempfile
import time
from argparse import ArgumentParser, Namespace

class Server:
    def __init__(self, args: Namespace, ports, password, channel, ipv6) -> None:
        self.ports = ports
        self.password = password
        self.ipv6 = ipv6

        if self.ipv6 and args.listen:
            self.address = socket.getaddrinfo(args.listen, None, proto=socket.IPPROTO_TCP)[0][4][0]
        elif args.listen:
            self.address = socket.gethostbyname(args.listen)
        else:
            self.address = ""
            server_name_limit = 63  # From the RFC.
            self.name = socket.getfqdn(self.address)[:server_name_limit].encode()
