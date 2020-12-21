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

        self.members_returns_socket: Dict[str, Socket] = {}
        self.socket_returns_members: Dict[Socket, str] = {}
        self.usernames_returns_nicknames: Dict[str, str] = {}  # nickname connected to username
        self.nicknames_returns_usernames: Dict[str, str] = {}

        self.threadID = threading.get_ident()
        self.serverSocket = serverSocket
        self.socketList = [serverSocket]
        # stores all the usernames in the channel
        self.clientList = []
        # stores all the nick names in the server

    def return_name_list(self):
        return self.clientList

    def update_dictionaries(self, client, client_socket, nickname):
        self.members_returns_socket[client] = client_socket
        self.socket_returns_members[client_socket] = client
        self.socketList.append(client_socket)
        # TODO should the usernames be stored here or the nicknames?
        self.clientList.append(client)

        self.usernames_returns_nicknames[client] = nickname
        self.nicknames_returns_usernames[nickname] = client

    def removeMember(self, client, client_socket):
        # Remove member from all dicts/lists
        del self.members_returns_socket[client]
        del self.socket_returns_members[client_socket]
        del self.nicknames_returns_usernames[self.usernames_returns_nicknames[client]]
        del self.usernames_returns_nicknames[client]
        self.socketList.remove(client_socket)
        self.clientList.remove(client)

    def addMember(self, client, nickname, client_address, hostname) -> bool:

        if nickname in self.nicknames_returns_usernames:
            print("Nickname clash")

            # ERR_NICKNAMEINUSE (433)
            textToSend = ":" + self.name + " 433 " + nickname + " :Nickname is already in use \r\n"
            self.server.sendMessage(client_address, textToSend)

            return False

        self.update_dictionaries(client, client_address, nickname)

        print("Member joined channel: " + self.name)

        # message = ":host MODE " + self.name + " +n \r\n"
        # self.server.sendMessage(client_address, message)

        # TODO here, should the nickname or the username be shown?
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

        return True

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

    # TODO make nick clashes
    def distribute_message(self, notified_socket, username, message, messagequery):

        # Send user and message (both with their headers) We are reusing here message header sent
        # by sender, and saved username header send by user when he connected client_socket.send(
        # user['header'] + user['msgData'] + message['header'] + message['msgData'])
        # textToSend = ":" + message + "!" + message + "@" + username + " PRIVMSG " + str(self.name) + " :" + \
        #             message  # NEED TO ENCODE AGAIN TO SEND

        textToSend = "NO TEXT SENT" # Something bad has happened if this stays as this

        if messagequery == "PRIVMSG":
            textToSend = ":" + username + "!" + self.server.name + "@" + self.server.name + " " + messagequery + " " + str(
                self.name) + " :" + \
                         message
        elif messagequery == "JOIN":
            textToSend = ":" + username + "!~" + username + "@" + self.server.name + " " + messagequery + " " + str(
                self.name) + " :" + message
        elif messagequery == "PART":
            textToSend = ":" + username + "!" + username + "@" + self.server.name + " " + messagequery + " " + str(
                self.name) + " :" + message
        elif messagequery == "QUIT":
            textToSend = ":" + username + "!" + username + "@" + self.server.name + " " + messagequery + " " + str(
                self.name) + " :" + message

        print(f'Sent Text: {textToSend}')

        # Iterate over connected clients and broadcast message
        for client_socket in self.socketList:
            if client_socket != self.serverSocket:
                # But don't sent it to sender
                if client_socket != notified_socket:
                    self.server.sendMessage(client_socket, textToSend)
