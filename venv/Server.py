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
    def __init__(self, ports, password, channel):
        self.ports = ports
        self.password = password
