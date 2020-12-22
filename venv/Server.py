import ipaddress
import socket
from datetime import datetime
import time
from typing import Dict
from Channel import Channel
import select

# import irc

Socket = socket.socket
MSGLEN = 2048


class Server:
    # https://github.com/jrosdahl/miniircd/blob/master/miniircd line 789
    def __init__(self, ports=None, ipv6="fc00:1337::17") -> None:

        # allows for the use of a custom port, if there is none given then use the default port
        if ports is None:
            ports = [6667]  # default port for server
        else:
            ports = [int(ports)]

        self.name = socket.gethostname()
        self.ipv6 = ipv6
        # self.ipv6 = "::1"

        self.version_number = 0.6
        self.created = datetime.today().strftime("at %X on %d %B, %Y")

        self.ports = ports
        self.serverSocket = Socket(family=socket.AF_INET6)

        # this means that you can reuse addresses for reconnection
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.socketList = [self.serverSocket]
        self.channels: Dict[str, Channel] = {}  # key: irc_lower(channelname)
        self.usernames_returns_sockets: Dict[str, Socket] = {}  # returns the socket for the user
        self.sockets_returns_username: Dict[Socket, str] = {}  # username connected to socket
        self.usernames_returns_nicknames: Dict[str, str] = {}  # nickname connected to username
        self.nicknames_returns_usernames: Dict[str, str] = {}  # username connected to nickname
        self.start_time = time.time()
        self.initialise_server()

    # updates the dictionaries when a new user connects
    def update_dicts(self, user_socket, name, nickname):
        self.socketList.append(user_socket)
        self.sockets_returns_username[user_socket] = name
        self.usernames_returns_sockets[name] = user_socket
        self.usernames_returns_nicknames[name] = nickname
        self.nicknames_returns_usernames[nickname] = name

    # creates a channel with a set name
    def add_channel(self, name="#test"):
        name = name[0:63]

        if name[0] == "#":
            channel = Channel(self, name, self.serverSocket)
            self.channels[name] = channel
        else:
            return None

        return channel

    def initialise_server(self):
        # bind the server ipv6 with the port and then listen to that socket
        try:
            self.serverSocket.bind((str(self.ipv6), self.ports[0]))
            self.serverSocket.listen()
        except:
            print("A binding error occurred, please make sure that you are binding a valid ipv6 address")
        self.add_channel()
        self.refresh_server()

    def init_reg(self) -> bool:
        # Accept new connection
        # That gives us new socket - client socket, connected to this given client only, it's unique for that client
        # The other returned object is ip/port set

        client_socket, client_address = self.serverSocket.accept()
        # Client should send his name right away, receive it
        cap = self.receive_message(client_socket)
        user = self.receive_message(client_socket)

        if not (cap and user):
            return False
        else:
            # split the user information when a space occurs so that we get an array of information
            userinfo = user.split()
            try:
                nickname = userinfo[1]
                username = userinfo[3]
            except:
                return False

            self.update_dicts(client_socket, username, nickname)

            # The following is according to https://modern.ircdocs.horse/#rplwelcome-001
            # Send the client the appropriate messages

            # RPL_WELCOME (001)
            text_to_send = ":" + self.name + " 001 " + nickname + " :Welcome to our IRC Server - " + nickname + "[!" + \
                           nickname + "@" + self.name + "]\r\n"
            self.send_message(client_socket, text_to_send)

            # RPL_YOURHOST (002)
            text_to_send = ":" + self.name + " 002 " + nickname + " :Your host is " + self.name + ", running version " \
                           + str(self.version_number) + "\r\n"
            self.send_message(client_socket, text_to_send)

            # RPL_CREATED (003)
            text_to_send = ":" + self.name + " 003 " + nickname + " :This server was created " + self.created + "\r\n"
            self.send_message(client_socket, text_to_send)

            # RPL_MYINFO (004)
            text_to_send = ":" + self.name + " 004 " + nickname + " " + self.name + " " + str(
                self.version_number) + "\r\n"
            self.send_message(client_socket, text_to_send)

            # ---- LUSER ----
            self.l_user(nickname, client_socket)

            # ---- MOTD ----
            self.motd(nickname, client_socket)

            return True

    # send the client the message of the day
    def motd(self, nickname, client_socket):
        # RPL_MOTDSTART (375)
        text_to_send = ":" + self.name + " 375 " + nickname + " :- +++ Message of the day +++ - \r\n"
        self.send_message(client_socket, text_to_send)

        # RPL_MOTD (372)
        text_to_send = ":" + self.name + " 372 " + nickname + " :  +++ GAME ON GAMERS +++ \r\n"
        self.send_message(client_socket, text_to_send)

        # RPL_MOTDEND (376)
        text_to_send = ":" + self.name + " 376 " + nickname + " :End of /MOTD command. \r\n"
        self.send_message(client_socket, text_to_send)

    # send the client the LUSER information, this concerns how many clients and channels there are
    def l_user(self, nickname, client_socket):
        # RPL_LUSERCLIENT (251)
        text_to_send = ":" + self.name + " 251 " + nickname + " :There are " + str(
            len(self.usernames_returns_nicknames)) + " users on 1 server \r\n"
        self.send_message(client_socket, text_to_send)

        # RPL_LUSEROP (252)
        text_to_send = ":" + self.name + " 252 " + nickname + " 0 :operator(s) online \r\n"
        self.send_message(client_socket, text_to_send)

        # RPL_LUSERUNKNOWN (253)
        text_to_send = ":" + self.name + " 253 " + nickname + " 0 :unknown connection(s) \r\n"
        self.send_message(client_socket, text_to_send)

        # RPL_LUSERCHANNELS(254)
        text_to_send = ":" + self.name + " 254 " + nickname + " 1 :channels formed \r\n"
        self.send_message(client_socket, text_to_send)

        # RPL_LUSERME (255)
        text_to_send = ":" + self.name + " 255 " + nickname + " :I have " + str(
            len(self.usernames_returns_nicknames)) + " clients and 0 servers \r\n"
        self.send_message(client_socket, text_to_send)

    # receives data from the client
    def receive_message(self, client_socket):
        try:
            chunk = client_socket.recv(MSGLEN).decode("UTF-8")  # receives data from the socket of the client
            if chunk:
                return chunk
            else:
                return None
        except:  # Connection interrupted during transmission
            return None

    # sends the message chunk by chunk
    def send_message(self, to_socket, msg):
        total_sent = 0
        while total_sent < len(msg):
            to_send = bytes(msg[total_sent:], "UTF-8")
            try:
                sent = to_socket.send(to_send)
            except:  # Connection dropped
                return
            total_sent = total_sent + sent

    def refresh_server(self):
        while True:  # constantly refreshes the server, checking for new information on the socket
            read_sockets, _, exception_sockets = select.select(self.socketList, [], self.socketList)

            for notified_socket in read_sockets:  # Iterate over notified sockets

                # If notified socket is a server socket - new connection, accept it
                if notified_socket == self.serverSocket:
                    if not self.init_reg():
                        continue

                # Else existing socket is sending a message
                else:
                    # Receive message
                    message = self.receive_message(notified_socket)

                    # If False, client disconnected, cleanup
                    if not message:
                        # Remove from list for socket.socket()
                        self.remove_client(self.sockets_returns_username[notified_socket], notified_socket)
                        continue

                    print("------message------")
                    print(message)

                    command_found = self.execute_commands(message, notified_socket)

                    if not command_found:
                        print("Command not found, an error may have occurred :(")

            # It's not really necessary to have this, but will handle some socket exceptions just in case
            for notified_socket in exception_sockets:
                self.remove_client(self.sockets_returns_username[notified_socket], notified_socket)

    def remove_client(self, client_name, client_socket):
        # print('Closed connection from: {}'.format(self.clientList[client]['msgData'].decode('utf-8')))

        # REMOVE FROM ALL CHANNELS
        for channel_name, channel in self.channels.items():
            user_list = channel.return_name_list()
            if client_name in user_list:
                # Send quit message to channel
                username = self.sockets_returns_username[client_socket]
                nick = self.usernames_returns_nicknames[username]
                server_channel = self.channels[channel_name]
                text_to_send = nick + " HAS LEFT CHANNEL" + "\r\n"

                server_channel.distribute_message(client_socket, username,
                                                  text_to_send, "QUIT")  # Send leave message to make all users in channel aware
                channel.remove_member(client_name, client_socket)

        # Remove from list for socket.socket()
        self.socketList.remove(client_socket)

        # Remove from our lists of users
        del self.sockets_returns_username[client_socket]
        del self.usernames_returns_sockets[client_name]
        del self.nicknames_returns_usernames[self.usernames_returns_nicknames[client_name]]
        del self.usernames_returns_nicknames[client_name]

    def execute_commands(self, message, user_socket) -> bool:
        if not message:
            return False
        try:
            messages_arr = message.split()
            command = messages_arr[0]
            related_data = messages_arr[1]
        except:  # Split failed return
            return False
        command_found = False
        if command == "JOIN":
            self.join_channel(related_data, user_socket)
            command_found = True
        elif command == "QUIT":
            print("REMOVING CLIENT: " + self.sockets_returns_username[user_socket])
            self.remove_client(self.sockets_returns_username[user_socket], user_socket)
            command_found = True
        elif command == "PING":
            command_found = True
            message = ":" + self.name + " PONG " + self.name + " :" + related_data + "\r\n"
            self.send_message(user_socket, message)
        elif command == "PONG":
            command_found = True
        elif command == "MODE":
            command_found = True
        elif command == "PART":
            channel = related_data
            username = self.sockets_returns_username[user_socket]
            nick = self.usernames_returns_nicknames[username]
            server_channel = self.channels[channel]
            text_to_send = nick + " HAS LEFT CHANNEL" + "\r\n"

            server_channel.distribute_message(user_socket, username,
                                              text_to_send,
                                              "PART")  # Send leave message to make all users in channel aware
            server_channel.remove_member(username, user_socket)

            message = ":" + username + " PART " + channel + "\r\n"
            self.send_message(user_socket, message)
            command_found = True
        elif command == "NAMES":
            command_found = True
            self.list_names(user_socket, related_data)
        elif command == "WHO":
            command_found = True
            # OLD IRC VERSION BUT LETS DO IT ANYWAY? 352 WHO
            self.list_names(user_socket, related_data)
        elif command == "PRIVMSG":
            command_found = True
            self.private_messaging(message, user_socket)
        elif command == "NICK":
            print("Nickname was meant to be set here")
            return False
        elif command == "USER":
            print("Username was meant to be set here")
            return False
        return command_found

    def join_channel(self, channel, client_socket):
        try:
            username = self.sockets_returns_username[client_socket]
            nick = self.usernames_returns_nicknames[username]

            server_channel = self.channels[channel]
            text_to_send = nick + " HAS JOINED THE CHANNEL" + "\r\n"

            # Send join message to make all users in channel aware
            server_channel.distribute_message(client_socket, username, text_to_send, "JOIN")

            server_channel = self.channels[channel]
            username = self.sockets_returns_username[client_socket]
            server_channel.add_member(username, nick, client_socket, self.name)
        except:
            server_channel = self.add_channel(channel)
            if server_channel:
                username = self.sockets_returns_username[client_socket]
                server_channel.add_member(self.sockets_returns_username[client_socket],
                                          self.usernames_returns_nicknames[username],
                                          client_socket, self.name)
            else:
                print("Server name was not accepted")

    def private_messaging(self, message, user_socket):
        print("sending private message")
        username = self.sockets_returns_username[user_socket]
        if " " in message:
            channel = message.split('PRIVMSG', 1)[1].split(' ', 1)[1].split(' ', 1)[0]
            # if the channel is the same as a user's name, it's a private (direct) message
            if self.nicknames_returns_usernames.get(channel):
                recipient_nickname = channel
                recipient_username = self.nicknames_returns_usernames[recipient_nickname]
                recipient_socket = self.usernames_returns_sockets[recipient_username]
                message_contents = message.split(':', 1)[1]
                message_to_send = ":" + username + "!" + self.name + " PRIVMSG " + recipient_nickname + " :" + \
                                  message_contents
                self.send_message(recipient_socket, message_to_send)
        else:
            return

        if ":" in message:
            priv_msg = message.split('PRIVMSG', 1)[1].split(':', 1)[1]
        else:
            return

        # finds the channel, if the channel does not exist, create a new channel
        if channel in self.channels:
            sending_channel = self.channels[channel]
            sending_channel.distribute_message(user_socket, username, priv_msg, "PRIVMSG")
        else:
            sending_channel = self.add_channel(channel)
            sending_channel.distribute_message(user_socket, username, priv_msg, "PRIVMSG")

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
            self.send_message(user_socket, message)
        else:
            username = self.sockets_returns_username[user_socket]
            channel = self.channels[channel_name]
            message = ":" + self.name + " 353 " + username + " = " + channel_name + " :" + channel.get_names(
                username) + "\r\n"
            self.send_message(user_socket, message)
