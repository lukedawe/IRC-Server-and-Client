import string
import threading
from typing import Any, Collection, Dict, List, Optional, Sequence, Set
# import Server
from Client import Client
import select

import socket

HEADER_LENGTH = 10

Socket = socket.socket

class Channel:
    # https://github.com/jrosdahl/miniircd/blob/master/miniircd line 47
    threadID = None

    def __init__(self, server: "Server", name: str, serverSocket) -> None:
        self.server = server
        self.name = name

        # TODO make sure that these dictionaries are kept up to date with eachtother
        self.members_returns_socket: Dict[str, Socket] = {}
        self.members_returns_name: Dict[Socket, str] = {}

        self.threadID = threading.get_ident()
        self.serverSocket = serverSocket
        self.socketList = [serverSocket]
        self.clientList = {}

    def addMember(self, client, client_address) -> None:
        print(client)
        print(client_address)
        self.members_returns_socket[client] = client_address
        print("Member joined channel: " + self.name)
        message = ":" + client + "!~" + client + "host" + " JOIN " + self.name
        self.sendMessage(client_address, message)

    def sendMessage(self, tosocket, msg):
        totalsent = 0
        while totalsent < len(msg):
            tosend = bytes(msg[totalsent:], "UTF-8")
            sent = tosocket.send(tosend)
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def removeMember(self, client):
        print('Closed connection from: {}'.format(self.clientList[client]['msgData'].decode('utf-8')))

        # Remove from list for socket.socket()
        self.socketList.remove(client)

        # Remove from our list of users
        del self.clientList[client]

    def distributeMessage(self):
        # Iterate over connected clients and broadcast message
        for client_socket in self.socketList:

            # But don't sent it to sender
            if client_socket != notified_socket:
                # Send user and message (both with their headers) We are reusing here message header sent
                # by sender, and saved username header send by user when he connected client_socket.send(
                # user['header'] + user['msgData'] + message['header'] + message['msgData'])

                textToSend = ":" + user['msgData'].decode("utf-8") + "!" + user['msgData'].decode(
                    "utf-8") + "@" + self.members[client_socket] + " PRIVMSG " + str(self.name) + " :" + \
                             message['msgData'].decode("utf-8")  # NEED TO ENCODE AGAIN TO SEND
                print(f'Sent Text: {textToSend}')
                textToSend = textToSend.encode()
                client_socket.send(textToSend)
