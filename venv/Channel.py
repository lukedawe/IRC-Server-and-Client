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
        self.socket_returns_members: Dict[Socket, str] = {}

        self.threadID = threading.get_ident()
        self.serverSocket = serverSocket
        self.socketList = [serverSocket]
        self.clientList = []
        self.clientNicknames = []

    def update_dictionaries(self, client, client_socket):
        self.members_returns_socket[client] = client_socket
        self.socket_returns_members[client_socket] = client
        self.socketList.append(client_socket)
        self.clientList.append(client)

    def addMember(self, client, nickname, client_address, hostname) -> None:

        if nickname in self.clientNicknames:
            print("Nickname clash")
            return

        self.update_dictionaries(client, client_address)

        print("Member joined channel: " + self.name)

        # message = ":host MODE " + self.name + " +n \r\n"
        # self.server.sendMessage(client_address, message)

        message = ":" + client + "!" + client + "@::1:6667" + " JOIN " + self.name + "\r\n"
        self.server.sendMessage(client_address, message)

        # RPL_NOTOPIC (331)
        textToSend = ":" + hostname + " 331 " + client + " " + self.name + " :No topic is set\r\n"
        self.server.sendMessage(client_address, textToSend)

        # RPL_NAMREPLY (353)
        message = ":" + hostname + " 353 " + client + " = " + self.name + " :" + self.get_names(
            client) + " " + client + "\r\n"
        self.server.sendMessage(client_address, message)

        # RPL_ENDOFNAMES(366)
        message = ":" + hostname + " 366 " + client + " " + self.name + " :" + "End of NAMES list" + "\r\n"
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


    # TODO make nick clashes
    def distribute_message(self, notified_socket, username, message):

        # Send user and message (both with their headers) We are reusing here message header sent
        # by sender, and saved username header send by user when he connected client_socket.send(
        # user['header'] + user['msgData'] + message['header'] + message['msgData'])
        # textToSend = ":" + message + "!" + message + "@" + username + " PRIVMSG " + str(self.name) + " :" + \
        #             message  # NEED TO ENCODE AGAIN TO SEND

        textToSend = ":" + username + "!" + self.server.name + "@" + self.server.name + " PRIVMSG " + str(
            self.name) + " :" + \
                     message  # NEED TO ENCODE AGAIN TO SEND

        print(f'Sent Text: {textToSend}')


        # Iterate over connected clients and broadcast message
        for client_socket in self.socketList:
            if client_socket != self.serverSocket:
                # But don't sent it to sender
                if client_socket != notified_socket:
                    self.server.sendMessage(client_socket, textToSend)
