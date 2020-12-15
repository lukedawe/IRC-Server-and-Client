import string
import threading
from typing import Any, Collection, Dict, List, Optional, Sequence, Set
import Server
from Client import Client
import select

HEADER_LENGTH = 10


class Channel:
    # https://github.com/jrosdahl/miniircd/blob/master/miniircd line 47
    threadID = None

    def __init__(self, server: "Server", name: bytes, serverSocket=[]) -> None:
        self.server = server
        self.name = name
        self.members = []
        self.threadID = threading.get_ident()
        self.socketList = [serverSocket]

    def addMember(self, client) -> None:
        self.members.append(client)

    def removeClient(self, client):
        pass

    def receiveMessage(self, clientSocket):
        try:
            messageHeader = clientSocket.recv(HEADER_LENGTH)

            if not len(messageHeader):
                return False

            messageLength = int(messageHeader.decode('utf-8').strip())
            return {'header': messageHeader, 'data': clientSocket.recv(messageLength)}

        except:
            return False

        self.socketList = self.socketList

        while True:
            read_sockets, _, exception_sockets = select.select(self.socketList, [], self.socketList)

            # Iterate over notified sockets
            for notified_socket in read_sockets:

                # If notified socket is a server socket - new connection, accept it
                if notified_socket == server_socket:

                    # Accept new connection
                    # That gives us new socket - client socket, connected to this given client only, it's unique for that client
                    # The other returned object is ip/port set
                    client_socket, client_address = server_socket.accept()

                    # Client should send his name right away, receive it
                    user = receive_message(client_socket)

                    # If False - client disconnected before he sent his name
                    if user is False:
                        continue

                    # Add accepted socket to select.select() list
                    self.socketList.append(client_socket)

                    # Also save username and username header
                    clients[client_socket] = user

                    print('Accepted new connection from {}:{}, username: {}'.format(*client_address,
                                                                                    user['data'].decode('utf-8')))

                # Else existing socket is sending a message
                else:

                    # Receive message
                    message = receive_message(notified_socket)

                    # If False, client disconnected, cleanup
                    if message is False:
                        print('Closed connection from: {}'.format(clients[notified_socket]['data'].decode('utf-8')))

                        # Remove from list for socket.socket()
                        self.socketList.remove(notified_socket)

                        # Remove from our list of users
                        del clients[notified_socket]

                        continue

                    # Get user by notified socket, so we will know who sent the message
                    user = clients[notified_socket]

                    print(f'Received message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}')

                    # Iterate over connected clients and broadcast message
                    for client_socket in clients:

                        # But don't sent it to sender
                        if client_socket != notified_socket:
                            # Send user and message (both with their headers)
                            # We are reusing here message header sent by sender, and saved username header send by user when he connected
                            client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])

            # It's not really necessary to have this, but will handle some socket exceptions just in case
            for notified_socket in exception_sockets:
                # Remove from list for socket.socket()
                self.socketList.remove(notified_socket)

                # Remove from our list of users
                del clients[notified_socket]


# from https://github.com/jrosdahl/miniircd/blob/master/miniircd lines 1053-1060
_ircstring_translation = bytes.maketrans(
    (string.ascii_lowercase.upper() + "[]\\^").encode(),
    (string.ascii_lowercase + "{}|~").encode(),
)


def irc_lower(s: bytes) -> bytes:
    return s.translate(_ircstring_translation)
