import ipaddress
import socket
import string
from datetime import datetime
import time
from typing import Dict
from Channel import Channel
import Client
import hashlib
import select

# import irc

Socket = socket.socket
MSGLEN = 2048


class Server:
    # https://github.com/jrosdahl/miniircd/blob/master/miniircd line 789
    def __init__(self, ports=None, password="", channel="test", ipv6=ipaddress.ip_address('::1')) -> None:
        if ports is None:
            ports = [6667]  # default port for server

        self.name = socket.gethostname()
        self.version_number = 0.5
        self.created = datetime.today().strftime("at %X on %d %B,%Y")

        self.ports = ports
        self.ipv6 = ipv6
        self.serverSocket = Socket(family=socket.AF_INET6)

        # this means that you can reuse addresses for reconnection
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.socketList = [self.serverSocket]
        self.channels: Dict[str, Channel] = {}  # key: irc_lower(channelname)
        # self.clients: Dict[Socket, Client] = {}
        self.usernames_returns_sockets: Dict[string, Socket] = {}  # username connected to socket
        self.sockets_returns_username: Dict[Socket, string] = {}  # username connected to socket
        self.nicknames: Dict[string, string] = {}  # nickname connected to username
        # self.threads: Dict[bytes, Channel] = {}
        self.start_time = time.time()
        self.initialiseServer()

    def update_dicts(self, user_socket, name, nickname):
        self.socketList.append(user_socket)
        self.sockets_returns_username[user_socket] = name
        self.usernames_returns_sockets[name] = user_socket
        self.nicknames[name] = nickname

    def addChannel(self, name="#test") -> Channel:
        name = name[0:63]
        channel = Channel(self, name, self.serverSocket)
        self.serverSocket.listen()
        # newThread = channel.threadID
        self.channels[name] = channel
        return channel

    def initialiseServer(self):
        # address = socket.getaddrinfo(str(self.ipv6), self.ports[0], proto=socket.IPPROTO_TCP)[0][4][0]
        # address = [addr for addr in socket.getaddrinfo(self.ipv6, None) if socket.AF_INET6 == addr[0]]

        self.serverSocket.bind((str(self.ipv6), self.ports[0]))
        self.serverSocket.listen()

        self.addChannel()

        self.refreshServer()

    def initReg(self) -> bool:
        # Accept new connection
        # That gives us new socket - client socket, connected to this given client only, it's unique for that client
        # The other returned object is ip/port set

        client_socket, client_address = self.serverSocket.accept()
        # Client should send his name right away, receive it
        cap = self.receiveMessage(client_socket)
        user = self.receiveMessage(client_socket)

        if not (cap and user):
            return False
        else:

            userinfo = user.split()
            nickname = userinfo[1]
            username = userinfo[3]

            self.update_dicts(client_socket, username, nickname)

            # The following is according to https://modern.ircdocs.horse/#rplwelcome-001

            # RPL_WELCOME (001)
            textToSend = ":" + self.name + " 001 " + nickname + " :Welcome the IRC Server " + nickname + "[!" + nickname + "@" + self.name + "]\r\n"
            self.sendMessage(client_socket, textToSend)

            # RPL_YOURHOST (002)
            textToSend = ":" + self.name + " 002 " + nickname + " :Your host is " + self.name + ", running version " + str(
                self.version_number) + \
                         "\r\n"
            self.sendMessage(client_socket, textToSend)

            # RPL_CREATED (003)
            textToSend = ":" + self.name + " 003 " + nickname + " :This server was created " + self.created + "\r\n"
            self.sendMessage(client_socket, textToSend)

            # RPL_MYINFO (004)
            textToSend = ":" + self.name + " 004 " + nickname + " " + self.name + " " + str(
                self.version_number) + " o o\r\n"
            self.sendMessage(client_socket, textToSend)

            # RPL_ISUPPORT (005)
            # textToSend = ":" + self.name + " 005 " + nickname + "CHARSET=ascii :are supported by this server \r\n"
            # self.sendMessage(client_socket, textToSend)

            # ---- LUSER ----
            self.luser(nickname, client_socket)

            # ---- MOTD ----
            self.motd(nickname, client_socket)

            return True

    def motd(self, nickname, client_socket):
        # RPL_MOTDSTART (375)
        textToSend = ":" + self.name + " 375 " + nickname + " :- " + self.name + " Message of the day - \r\n"
        self.sendMessage(client_socket, textToSend)

        # RPL_MOTD (372)
        textToSend = ":" + self.name + " 372 " + nickname + " :G'DAY MADLADZ \r\n"
        self.sendMessage(client_socket, textToSend)

        # RPL_MOTDSTART (376)
        textToSend = ":" + self.name + " 376 " + nickname + " :End of /MOTD command. \r\n"
        self.sendMessage(client_socket, textToSend)

    def luser(self, nickname, client_socket):
        # RPL_LUSERCLIENT (251)
        textToSend = ":" + self.name + " 251 " + nickname + " :There are " + str(
            len(self.nicknames)) + " users and 0 services on 1 server \r\n"
        self.sendMessage(client_socket, textToSend)

        # RPL_LUSEROP (252)
        textToSend = ":" + self.name + " 252 " + nickname + " 0 :operator(s) online \r\n"
        self.sendMessage(client_socket, textToSend)

        # RPL_LUSERUNKNOWN (253)
        textToSend = ":" + self.name + " 253 " + nickname + " 0 :unknown connection(s) \r\n"
        self.sendMessage(client_socket, textToSend)

        # RPL_LUSERCHANNELS(254)
        textToSend = ":" + self.name + " 254 " + nickname + " 1 :channels formed \r\n"
        self.sendMessage(client_socket, textToSend)

        # RPL_LUSERME (255)
        textToSend = ":" + self.name + " 255 " + nickname + " :I have " + str(
            len(self.nicknames)) + " clients and 0 servers \r\n"
        self.sendMessage(client_socket, textToSend)

    def receiveMessage(self, clientSocket):
        try:
            chunk = clientSocket.recv(MSGLEN).decode("UTF-8")
            if chunk:
                return chunk
            else:
                return None
        except: # Connection interrupted during transmission
            return None

    def sendMessage(self, tosocket, msg):
        # print("SENT CHUNK: " + msg)
        total_sent = 0
        while total_sent < len(msg):
            to_send = bytes(msg[total_sent:], "UTF-8")
            try:
                sent = tosocket.send(to_send)
            except: # Connection dropped
                return
            total_sent = total_sent + sent

    def refreshServer(self):
        while True:

            read_sockets, _, exception_sockets = select.select(self.socketList, [], self.socketList)

            # Iterate over notified sockets
            for notified_socket in read_sockets:

                # If notified socket is a server socket - new connection, accept it
                if notified_socket == self.serverSocket:
                    if not self.initReg():
                        continue

                # Else existing socket is sending a message
                else:

                    # Receive message
                    message = self.receiveMessage(notified_socket)

                    # If False, client disconnected, cleanup
                    if not message:
                        # Remove from list for socket.socket()
                        # TODO we need to find the channel that the user is in so that we can remove the client from
                        #   those lists
                        self.removeClient(self.sockets_returns_username[notified_socket], notified_socket)
                        continue

                    print("------message------")
                    print(message)

                    command_found = self.executeCommands(message, notified_socket)

                    # We now want to see what channel the client is in, and send their message to the rest of the
                    #   clients in that channel.

                    """
                    print(
                        f'Received message from {user["msgData"].decode("utf-8")}: {message["msgData"].decode("utf-8")}')
                    """
            # It's not really necessary to have this, but will handle some socket exceptions just in case
            for notified_socket in exception_sockets:
                # TODO we need to find the channel that the user is in so that we can remove the client from
                #   those lists
                self.removeClient(self.sockets_returns_username[notified_socket], notified_socket)

    def removeClient(self, client_name, client_socket):
        # print('Closed connection from: {}'.format(self.clientList[client]['msgData'].decode('utf-8')))

        # Remove from list for socket.socket()
        self.socketList.remove(client_socket)

        # Remove from our lists of users
        del self.sockets_returns_username[client_socket]
        del self.usernames_returns_sockets[client_name]
        del self.nicknames[client_name]

    # TODO Private direct messaging

    def executeCommands(self, message, user_socket) -> bool:
        if not message:
            return False
        try:
            messagesArr = message.split()
            command = messagesArr[0]
            relatedData = messagesArr[1]
        except: # Split failed return
            return False
        command_found = False
        if command == "JOIN":
            self.joinChannel(relatedData, user_socket)
            command_found = True
        elif command == "PING":
            command_found = True
            message = ":" + self.name + " PONG " + self.name + " :" + relatedData + "\r\n"
            self.sendMessage(user_socket, message)
        elif command == "PONG":
            command_found = True
            pass
        elif command == "MODE":
            command_found = True
            pass
        elif command == "NAMES":
            command_found = True
            users = ""
            item = False
            for peers in self.nicknames:
                if not item:
                    users += peers
                    item = True
                else:
                    users += " " + peers

            print(users)

            message = ":" + self.name + " 353 " + self.sockets_returns_username[user_socket] + " @ " + relatedData + " :" + users + "\r\n"
            self.sendMessage(user_socket, message)
            pass
        elif command == "WHO":
            command_found = True

            # OLD IRC VERSION BUT LETS DO IT ANYWAY? 352 WHO
            if relatedData in self.nicknames:
                # DUNNO message = ":" + self.name + " 352 " + self.sockets_returns_username[user_socket] + " :" + relatedData + "\r\n"
                self.sendMessage(user_socket, message)
            else:
                message = ":" + self.name + " 315 " + self.sockets_returns_username[user_socket] + " " + relatedData + " :End of /WHO list\r\n"
                self.sendMessage(user_socket, message)
            pass
        elif command == "PRIVMSG":
            print("sending private message")
            if " " in message:
                channel = message.split('PRIVMSG', 1)[1].split(' ', 1)[1].split(' ', 1)[0]
            if ":" in message:
                PRIVMSG = message.split('PRIVMSG', 1)[1].split(':', 1)[1]

            if channel in self.channels:
                sending_channel = self.channels[channel]
                sending_channel.distribute_message(user_socket, self.sockets_returns_username[user_socket], PRIVMSG)
            else:
                self.addChannel(channel)
                sending_channel = self.channels[channel]
                sending_channel.distribute_message(user_socket, self.sockets_returns_username[user_socket], PRIVMSG)

        return command_found

    # TODO this has to be made so that (if a channel doesn't exist) the channel is created,
    #   if it does already exist, the client has to be entered into it.
    def joinChannel(self, channel, client_socket):
        try:
            server_channel = self.channels[channel]
            username = self.sockets_returns_username[client_socket]
            server_channel.addMember(self.sockets_returns_username[client_socket], self.nicknames[username],
                                     client_socket, self.name)
        except:
            server_channel = self.addChannel(channel)
            username = self.sockets_returns_username[client_socket]
            server_channel.addMember(self.sockets_returns_username[client_socket], self.nicknames[username],
                                     client_socket, self.name)


# from https://github.com/jrosdahl/miniircd/blob/master/miniircd lines 1053-1060
_ircstring_translation = bytes.maketrans(
    (string.ascii_lowercase.upper() + "[]\\^").encode(),
    (string.ascii_lowercase + "{}|~").encode(),
)


def irc_lower(s: bytes) -> bytes:
    return s.translate(_ircstring_translation)

# TODO
