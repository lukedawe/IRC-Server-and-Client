import logging
import os
import re
import select
import socket
import string
import sys
import tempfile
import time
from argparse import Namespace


class Server:
    def __init__(self, args: Namespace) -> None:
        self.ports = args.ports
        self.password = args.password
