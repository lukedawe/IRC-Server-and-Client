import string
import threading
from typing import Any, Collection, Dict, List, Optional, Sequence, Set
# import Server
from Client import Client
import select

HEADER_LENGTH = 10


class Channel:
    # https://github.com/jrosdahl/miniircd/blob/master/miniircd line 47
    threadID = None

    def __init__(self, server: "Server", name: bytes, serverSocket) -> None:
        self.server = server
        self.name = name
        self.members = []
        self.threadID = threading.get_ident()
        self.serverSocket = serverSocket
        self.socketList = [serverSocket]
        self.clientList = {}

    def addMember(self, client) -> None:
        self.members.append(client)

    def removeClient(self, client):
        print('Closed connection from: {}'.format(self.clientList[client]['msgData'].decode('utf-8')))

        # Remove from list for socket.socket()
        self.socketList.remove(client)

        # Remove from our list of users
        del self.clientList[client]

    def receiveMessage(self, clientSocket):
        try:
            messageHeader = clientSocket.recv(HEADER_LENGTH)

            if not len(messageHeader):
                return False

            messageLength = int(messageHeader.decode('utf-8').strip())
            return {'header': messageHeader, 'msgData': clientSocket.recv(messageLength)}

        except:
            return False

    def refreshChannel(self):
        while True:
            read_sockets, _, exception_sockets = select.select(self.socketList, [], self.socketList)

            # Iterate over notified sockets
            for notified_socket in read_sockets:

                # If notified socket is a server socket - new connection, accept it
                if notified_socket == self.serverSocket:

                    # Accept new connection
                    # That gives us new socket - client socket, connected to this given client only, it's unique for that client
                    # The other returned object is ip/port set
                    client_socket, client_address = self.serverSocket.accept()

                    # Client should send his name right away, receive it
                    user = self.receiveMessage(client_socket)

                    # If False - client disconnected before he sent his name
                    if user is False:
                        continue

                    # Add accepted socket to select.select() list
                    self.socketList.append(client_socket)

                    # Also save username and username header
                    self.clientList[client_socket] = user

                    print('Accepted new connection from {}:{} username: {}'.format(client_address[0], client_address[1], user['msgData'].decode('utf-8')))

                # Else existing socket is sending a message
                else:

                    # Receive message
                    message = self.receiveMessage(notified_socket)

                    # If False, client disconnected, cleanup
                    if message is False:
                        # Remove from list for socket.socket()
                        self.removeClient(notified_socket)

                        continue

                    # Get user by notified socket, so we will know who sent the message
                    user = self.clientList[notified_socket]

                    print(f'Received message from {user["msgData"].decode("utf-8")}: {message["msgData"].decode("utf-8")}')

                    # Iterate over connected clients and broadcast message
                    for client_socket in self.clientList:

                        # But don't sent it to sender
                        if client_socket != notified_socket:
                            # Send user and message (both with their headers)
                            # We are reusing here message header sent by sender, and saved username header send by user when he connected
                            client_socket.send(user['header'] + user['msgData'] + message['header'] + message['msgData'])

            # It's not really necessary to have this, but will handle some socket exceptions just in case
            for notified_socket in exception_sockets:
                # Remove from list for socket.socket()
                self.socketList.removeClient(notified_socket)

                # Remove from our list of users
                del self.clientList[notified_socket]


# from https://github.com/jrosdahl/miniircd/blob/master/miniircd lines 1053-1060
_ircstring_translation = bytes.maketrans(
    (string.ascii_lowercase.upper() + "[]\\^").encode(),
    (string.ascii_lowercase + "{}|~").encode(),
)


def irc_lower(s: bytes) -> bytes:
    return s.translate(_ircstring_translation)
