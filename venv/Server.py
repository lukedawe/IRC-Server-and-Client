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
    def __init__(self, ports=None, channel="test", ipv6=ipaddress.ip_address('::1')) -> None:
        if ports is None:
            ports = [6667]  # default port for server

        self.name = socket.gethostname()
        self.version_number = 0.6
        self.created = datetime.today().strftime("at %X on %d %B, %Y")

        self.ports = ports
        self.ipv6 = ipv6
        self.serverSocket = Socket(family=socket.AF_INET6)

        # this means that you can reuse addresses for reconnection
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.socketList = [self.serverSocket]
        self.channels: Dict[str, Channel] = {}  # key: irc_lower(channelname)
        # self.clients: Dict[Socket, Client] = {}
        self.usernames_returns_sockets: Dict[str, Socket] = {}  # username connected to socket
        self.sockets_returns_username: Dict[Socket, str] = {}  # username connected to socket
        self.usernames_returns_nicknames: Dict[str, str] = {}  # nickname connected to username
        self.nicknames_returns_usernames: Dict[str, str] = {}
        # self.threads: Dict[bytes, Channel] = {}
        self.start_time = time.time()
        self.initialiseServer()

    # updates the dictionaries when a new user connects
    def update_dicts(self, user_socket, name, nickname):
        self.socketList.append(user_socket)
        self.sockets_returns_username[user_socket] = name
        self.usernames_returns_sockets[name] = user_socket
        self.usernames_returns_nicknames[name] = nickname
        self.nicknames_returns_usernames[nickname] = name

    # creates a channel with a set name
    def addChannel(self, name="#test") -> Channel:
        name = name[0:63]
        channel = Channel(self, name, self.serverSocket)
        self.serverSocket.listen()
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
            textToSend = ":" + self.name + " 001 " + nickname + " :Welcome to our IRC Server - " + nickname + "[!" + nickname + "@" + self.name + "]\r\n"
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
                self.version_number) + "\r\n"
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
        textToSend = ":" + self.name + " 375 " + nickname + " :- +++ Message of the day +++ - \r\n"
        self.sendMessage(client_socket, textToSend)

        # RPL_MOTD (372)
        textToSend = ":" + self.name + " 372 " + nickname + " : +++ G'DAY MADLADZ +++ \r\n"
        textToSend = ":" + self.name + " 372 " + nickname + " :  +++ GAME ON GAMERS +++ \r\n"
        self.sendMessage(client_socket, textToSend)

        # RPL_MOTDEND (376)
        textToSend = ":" + self.name + " 376 " + nickname + " :End of /MOTD command. \r\n"
        self.sendMessage(client_socket, textToSend)

    def luser(self, nickname, client_socket):
        # RPL_LUSERCLIENT (251)
        textToSend = ":" + self.name + " 251 " + nickname + " :There are " + str(
            len(self.usernames_returns_nicknames)) + " users on 1 server \r\n"
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
            len(self.usernames_returns_nicknames)) + " clients and 0 servers \r\n"
        self.sendMessage(client_socket, textToSend)

    def receiveMessage(self, clientSocket):
        try:
            chunk = clientSocket.recv(MSGLEN).decode("UTF-8")
            if chunk:
                return chunk
            else:
                return None
        except:  # Connection interrupted during transmission
            return None

    def sendMessage(self, to_socket, msg):
        # print("SENT CHUNK: " + msg)
        total_sent = 0
        while total_sent < len(msg):
            to_send = bytes(msg[total_sent:], "UTF-8")
            try:
                sent = to_socket.send(to_send)
            except:  # Connection dropped
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
                self.removeClient(self.sockets_returns_username[notified_socket], notified_socket)

    def removeClient(self, client_name, client_socket):
        # print('Closed connection from: {}'.format(self.clientList[client]['msgData'].decode('utf-8')))

        # REMOVE FROM ALL CHANNELS
        for channelname, channel in self.channels.items():
            userlist = channel.return_name_list()
            if client_name in userlist:
                # Send quit message to channel
                username = self.sockets_returns_username[client_socket]
                nick = self.usernames_returns_nicknames[username]
                server_channel = self.channels[channelname]
                textToSend = nick + " HAS LEFT CHANNEL" + "\r\n"

                server_channel.distribute_message(client_socket, username,
                                                  textToSend)  # Send leave message to make all users in channel aware
                channel.removeMember(client_name, client_socket)

        # Remove from list for socket.socket()
        self.socketList.remove(client_socket)

        # Remove from our lists of users
        del self.sockets_returns_username[client_socket]
        del self.usernames_returns_sockets[client_name]
        del self.nicknames_returns_usernames[self.usernames_returns_nicknames[client_name]]
        del self.usernames_returns_nicknames[client_name]

    def executeCommands(self, message, user_socket) -> bool:
        if not message:
            return False
        try:
            messagesArr = message.split()
            command = messagesArr[0]
            relatedData = messagesArr[1]
        except:  # Split failed return
            return False
        command_found = False
        if command == "JOIN":
            self.joinChannel(relatedData, user_socket)
            command_found = True
        elif command == "QUIT":
            print("REMOVING CLIENT: " + self.sockets_returns_username[user_socket])
            self.removeClient(self.sockets_returns_username[user_socket], user_socket)
            command_found = True
        elif command == "PING":
            command_found = True
            message = ":" + self.name + " PONG " + self.name + " :" + relatedData + "\r\n"
            self.sendMessage(user_socket, message)
        elif command == "PONG":
            command_found = True
        elif command == "MODE":
            command_found = True
        elif command == "PART":
            channel = relatedData
            username = self.sockets_returns_username[user_socket]
            nick = self.usernames_returns_nicknames[username]
            server_channel = self.channels[channel]
            textToSend = nick + " HAS LEFT CHANNEL" + "\r\n"

            server_channel.distribute_message(user_socket, username,
                                              textToSend)  # Send leave message to make all users in channel aware
            server_channel.removeMember(username, user_socket)

            message = ":" + username + " PART " + channel + "\r\n"
            self.sendMessage(user_socket, message)
            command_found = True
        elif command == "NAMES":
            command_found = True
            self.list_names(user_socket, relatedData)
        elif command == "WHO":
            command_found = True
            # OLD IRC VERSION BUT LETS DO IT ANYWAY? 352 WHO
            self.list_names(user_socket, relatedData)
        elif command == "PRIVMSG":
            self.private_messaging(message, user_socket)
        return command_found

    def joinChannel(self, channel, client_socket):
        try:
            username = self.sockets_returns_username[client_socket]
            nick = self.usernames_returns_nicknames[username]

            server_channel = self.channels[channel]
            textToSend = nick + " HAS JOINED THE CHANNEL" + "\r\n"

            # Send join message to make all users in channel aware
            server_channel.distribute_message(client_socket, username, textToSend)

            server_channel = self.channels[channel]
            username = self.sockets_returns_username[client_socket]
            server_channel.addMember(username, nick, client_socket, self.name)
        except:
            server_channel = self.addChannel(channel)
            username = self.sockets_returns_username[client_socket]
            server_channel.addMember(self.sockets_returns_username[client_socket],
                                     self.usernames_returns_nicknames[username],
                                     client_socket, self.name)

    def private_messaging(self, message, user_socket):
        print("sending private message")
        username = self.sockets_returns_username[user_socket]
        if " " in message:
            channel = message.split('PRIVMSG', 1)[1].split(' ', 1)[1].split(' ', 1)[0]
            # if the channel is the same as a user's name, it's a private (direct) message
            if self.nicknames_returns_usernames.get(channel):
                direct_message = True
                recipient_nickname = channel
                recipient_username = self.nicknames_returns_usernames[recipient_nickname]
                recipient_socket = self.usernames_returns_sockets[recipient_username]
                message_contents = message.split(':', 1)[1]
                message_to_send = ":" + username + "!" + self.name + " PRIVMSG " + recipient_nickname + " :" + \
                                  message_contents
                self.sendMessage(recipient_socket, message_to_send)
        else:
            return

        if ":" in message:
            PRIVMSG = message.split('PRIVMSG', 1)[1].split(':', 1)[1]
        else:
            return

        if channel in self.channels:
            sending_channel = self.channels[channel]
            sending_channel.distribute_message(user_socket, username, PRIVMSG)
        else:
            self.addChannel(channel)
            sending_channel = self.channels[channel]
            sending_channel.distribute_message(user_socket, username, PRIVMSG)

    def list_names(self, user_socket, channel_name):
        if channel_name == "localhost":
            users = ""
            item = False
            for peers in self.usernames_returns_nicknames:
                if not item:
                    users += peers
                    item = True
                else:
                    users += " " + peers
            message = ":" + self.name + " 353 " + self.sockets_returns_username[
                user_socket] + " @ " + channel_name + " :" + users + "\r\n"
            self.sendMessage(user_socket, message)
        else:
            username = self.sockets_returns_username[user_socket]
            channel = self.channels[channel_name]
            message = ":" + self.name + " 353 " + username + " = " + channel_name + " :" + channel.get_names(
                username) + "\r\n"
            command_found = True
            self.sendMessage(user_socket, message)

    # if the username and the nickname isn't the same...

    # TODO when the bot sends two messages at once, only one appears
