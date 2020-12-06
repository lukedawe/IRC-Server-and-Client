import logging
import os
import re
import select
import socket
import string
import sys
import tempfile
import time


class Server:
    def __init__(self, ports, password, channel, ipv6, listen):
        self.ports = ports
        self.password = password
        self.ipv6 = ipv6

        if self.ipv6 and listen:
            self.address = socket.getaddrinfo(listen, None, proto=socket.IPPROTO_TCP)[0][4][0]
        elif listen:
            self.address = socket.gethostbyname(listen)
        else:
            self.address = ""
            server_name_limit = 63  # From the RFC.
            self.name = socket.getfqdn(self.address)[:server_name_limit].encode()
