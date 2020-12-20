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

        # TODO make sure that these dictionaries are kept up to date with each other
        self.members_returns_socket: Dict[str, Socket] = {}
        self.members_returns_name: Dict[Socket, str] = {}

        self.threadID = threading.get_ident()
        self.serverSocket = serverSocket
        self.socketList = [serverSocket]
        self.clientList = []

    def addMember(self, client, client_address) -> None:
        print(client)
        print(client_address)
        self.members_returns_socket[client] = client_address
        self.clientList.append(client)
        print("Member joined channel: " + self.name)

        message = ":host MODE " + self.name + " +n \r\n"
        self.server.sendMessage(client_address, message)

        message = ":" + client + "!~" + client + " host" + " JOIN " + self.name + "\r\n"
        self.server.sendMessage(client_address, message)

        message = client + " @ " + self.name + " :" + self.get_names(client) + "\r\n"
        self.server.sendMessage(client_address, message)

        message = client + " " + self.name + " :" + "End of /NAMES list." + "\r\n"
        self.server.sendMessage(client_address, message)

    def get_names(self, client):
        name_list = ""
        for name in self.clientList:
            if name == client:
                name = "@" + client
            if name_list:
                name_list = name_list + " " + name
            else:
                name_list = name
        return name_list

    def remove_member(self, client):
        print('Closed connection from: {}'.format(self.clientList[client]['msgData'].decode('utf-8')))

        # Remove from list for socket.socket()
        self.socketList.remove(client)

        # Remove from our list of users
        del self.clientList[client]

    def distribute_message(self, notified_socket, user, message):
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
