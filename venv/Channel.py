import threading
from typing import Dict
import socket

HEADER_LENGTH = 10

Socket = socket.socket


class Channel:
    # https://github.com/jrosdahl/miniircd/blob/master/miniircd line 47
    threadID = None

    def __init__(self, server, name: str, server_socket) -> None:
        self.server = server
        self.name = name
        print("CHANNEL NAME:" + self.name)

        self.members_returns_socket: Dict[str, Socket] = {}
        self.socket_returns_members: Dict[Socket, str] = {}
        self.usernames_returns_nicknames: Dict[str, str] = {}  # nickname connected to username
        self.nicknames_returns_usernames: Dict[str, str] = {}

        self.threadID = threading.get_ident()
        self.serverSocket = server_socket
        self.socketList = [server_socket]
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
        self.clientList.append(nickname)

        self.usernames_returns_nicknames[client] = nickname
        self.nicknames_returns_usernames[nickname] = client

    def remove_member(self, client, client_socket):
        print("MEMBER REMOVED-" + client)
        # Remove member from all dicts/lists
        del self.members_returns_socket[client]
        del self.socket_returns_members[client_socket]
        del self.nicknames_returns_usernames[self.usernames_returns_nicknames[client]]
        del self.usernames_returns_nicknames[client]
        self.socketList.remove(client_socket)
        self.clientList.remove(client)

    def add_member(self, client, nickname, client_address, hostname) -> bool:

        """if nickname in self.nicknames_returns_usernames:
            print("Nickname clash")

            # ERR_NICKNAMEINUSE (433)
            text_to_send = ":" + self.name + " 433 " + nickname + " :Nickname is already in use \r\n"
            self.server.send_message(client_address, text_to_send)

            return False"""

        self.update_dictionaries(client, client_address, nickname)

        print("LIST OF CLIENTS")
        print(self.clientList)
        print("Member joined channel: " + self.name)

        # message = ":host MODE " + self.name + " +n \r\n"
        # self.server.sendMessage(client_address, message)

        # TODO here, should the nickname or the username be shown?
        message = ":" + nickname + "!~" + client + "@::1:6667" + " JOIN " + self.name + "\r\n"
        self.server.send_message(client_address, message)

        # RPL_NOTOPIC (331)
        text_to_send = ":" + hostname + " 331 " + client + " " + nickname + " :No topic is set\r\n"
        self.server.send_message(client_address, text_to_send)

        # RPL_NAMREPLY (353)
        message = ":" + hostname + " 353 " + client + " = " + nickname + " :" + self.get_names(client) + " " + client + "\r\n"
        self.server.send_message(client_address, message)

        # RPL_ENDOFNAMES(366)
        message = ":" + hostname + " 366 " + client + " " + nickname + " :" + "End of NAMES list" + "\r\n"
        self.server.send_message(client_address, message)

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
    def distribute_message(self, notified_socket, username, message, message_query):
        print(username)
        print(self.usernames_returns_nicknames)
        if username in self.usernames_returns_nicknames:
            nickname = self.usernames_returns_nicknames[username]

        # Send user and message (both with their headers) We are reusing here message header sent
        # by sender, and saved username header send by user when he connected client_socket.send(
        # user['header'] + user['msgData'] + message['header'] + message['msgData'])
        # textToSend = ":" + message + "!" + message + "@" + username + " PRIVMSG " + str(self.name) + " :" + \
        #             message  # NEED TO ENCODE AGAIN TO SEND

        text_to_send = "NO TEXT SENT"  # Something bad has happened if this stays as this

        if message_query == "PRIVMSG":
            text_to_send = ":" + nickname + "!" + username + "@" + self.server.name + " " + message_query + " " \
                           + str(self.name) + " :" + message
        elif message_query == "JOIN":
            text_to_send = ":" + nickname + "!~" + username + "@" + self.server.name + " " + message_query + " " + str(
                self.name) + " :" + message
        elif message_query == "PART":
            text_to_send = ":" + nickname + "!" + username + "@" + self.server.name + " " + message_query + " " + str(
                self.name) + " :" + message
        elif message_query == "QUIT":
            text_to_send = ":" + nickname + "!" + username + "@" + self.server.name + " " + message_query + " " + str(
                self.name) + " :" + message

        print(f'Sent Text: {text_to_send}')

        # Iterate over connected clients and broadcast message
        for client_socket in self.socketList:
            if client_socket != self.serverSocket:
                # But don't sent it to sender
                if client_socket != notified_socket:
                    self.server.send_message(client_socket, text_to_send)
