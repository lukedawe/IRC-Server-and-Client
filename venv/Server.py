from argparse import Namespace


class Server:
    def __init__(self, args: Namespace) -> None:
        self.ports = args.ports
        self.password = args.password
