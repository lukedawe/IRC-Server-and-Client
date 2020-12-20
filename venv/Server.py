import ipaddress
import socket
import string
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
        self.members = {}
        if ports is None:
            ports = [6667]  # default port for server

        self.ports = ports
        self.ipv6 = ipv6
        self.socketList = []
        self.serverSocket = Socket(family=socket.AF_INET6)

        # self.listen = listen
        # self.serverSocket.listen()

        # this means that you can reuse addresses for reconnection
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        """
        if not password:
            self.password = hashlib.sha224(b"password").hexdigest()
        else:
            self.password = password
   
        if self.ipv6:
            self.address = socket.getaddrinfo(listen, None, proto=self.serverSocket.IPPROTO_TCP)
        else:
            self.ipv6 = "[::1]"
            server_name_limit = 63  # This is from RFC.
            self.name = socket.getfqdn()[:server_name_limit].encode()
            print("Socket = " + socket.getfqdn())
        """

        self.socketList = [self.serverSocket]
        self.channels: Dict[str, Channel] = {}  # key: irc_lower(channelname)
        # self.clients: Dict[Socket, Client] = {}
        self.usernames_returns_sockets: Dict[string, Socket] = {}  # username connected to socket
        self.usernames_returns_username: Dict[Socket, string] = {}  # username connected to socket
        self.nicknames: Dict[string, string] = {}  # nickname connected to username
        # self.threads: Dict[bytes, Channel] = {}
        self.initialiseServer()

    def addChannel(self, name="test") -> Channel:
        name = "#" + name  # RCD channel names have to start with a hashtag
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
        """
        for port in self.ports:
            s = socket.socket(
                socket.AF_INET6 if self.ipv6 else socket.AF_INET,
                socket.SOCK_STREAM,
            )
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.ipv6, port))
            s.listen(5)
            self.socketList.append(s)


        self.serverSocket.bind((Socket, bytes(self.ports[0])))
        self.serverSocket.listen()
        """

    # TODO find what channel the client wants to join
    # TODO add that client to the list of channel members
    def initReg(self) -> bool:
        # Accept new connection
        # That gives us new socket - client socket, connected to this given client only, it's unique for that client
        # The other returned object is ip/port set

        client_socket, client_address = self.serverSocket.accept()
        # Client should send his name right away, receive it
        cap = self.reveiveMessage(client_socket)
        user = self.reveiveMessage(client_socket)

        if not (cap and user):
            return False
        else:

            userinfo = user.split()
            nickname = userinfo[1]
            username = userinfo[3]

            self.usernames_returns_sockets[username] = client_socket

            self.nicknames[nickname] = username

            # print("message data: " + user['msgData'].decode('utf-8'))
            address = str(client_address[0])
            port = int(client_address[1])

            # OSError: [WinError 10022] An invalid argument was supplied
            # commented out the binding as that seemed to be causing the issue
            # client_socket.bind((address, port))
            # also, miniircd does not try to bind the port when a new client connects

            # Add accepted socket to select.select() list
            self.socketList.append(client_socket)

            # Also save username and username header
            self.usernames_returns_username[client_socket] = username

            # The following is according to https://modern.ircdocs.horse/#rplwelcome-001
            # hope that helps you :)

            textToSend = nickname + " :Welcome to the to the something Network, " + nickname + "!" + nickname + "@" + \
                         str(self.ports[0]) + "\r\n"
            print(f'Sent Text: {textToSend}')

            self.sendMessage(client_socket, textToSend)

            textToSend = nickname + " :Your host is <servername>, running version <version> \r\n"
            print(f'Sent Text: {textToSend}')

            self.sendMessage(client_socket, textToSend)

            textToSend = nickname + "<servername> <version> <available user modes> <available channel modes> " \
                                    "[<channel modes with a parameter>] \r\n"
            print(f'Sent Text: {textToSend}')

            self.sendMessage(client_socket, textToSend)

            textToSend = nickname + "<1-13 tokens> :are supported by this server \r\n"
            print(f'Sent Text: {textToSend}')

            self.sendMessage(client_socket, textToSend)

            '''
            address = str(client_address[0]) + ":" + str(client_address[1])
            
            # And add member
            self.addMember(client_socket, address)
    
            print('Accepted new connection from {} username: {}'.format(address,
                                                                        user['msgData'].decode('utf-8')))
    
            textToSend = ":" + user['msgData'].decode("utf-8") + "!~" + user['msgData'].decode(
                "utf-8") + "@" + self.members[client_socket] + " JOIN " + self.name
            print(f'Sent Text: {textToSend}')
    
            textToSend = textToSend.encode()
            client_socket.send(textToSend)#
            '''

            return True

    def reveiveMessage(self, clientSocket):
        chunk = clientSocket.recv(MSGLEN).decode("UTF-8")
        if chunk:
            return chunk
        else:
            return None

    def sendMessage(self, tosocket, msg):
        totalsent = 0
        while totalsent < len(msg):
            tosend = bytes(msg[totalsent:], "UTF-8")
            sent = tosocket.send(tosend)
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

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
                    message = self.reveiveMessage(notified_socket)

                    # If False, client disconnected, cleanup
                    if message is False:
                        # Remove from list for socket.socket()
                        self.removeClient(notified_socket)
                        continue

                    print(message)

                    # Get user by notified socket, so we will know who sent the message
                    user = self.usernames_returns_username[notified_socket]

                    command_found = self.executeCommands(message, notified_socket)

                    # We now want to see what channel the client is in, and send their message to the rest of the
                    #   clients in that channel.

                    """
                    print(
                        f'Received message from {user["msgData"].decode("utf-8")}: {message["msgData"].decode("utf-8")}')
                    """
            # It's not really necessary to have this, but will handle some socket exceptions just in case
            for notified_socket in exception_sockets:
                # Remove from list for socket.socket()
                self.socketList.pop(notified_socket)

                # Remove from our list of users
                del self.usernames_returns_username[notified_socket]

    def addMember(self, client, clientaddress) -> None:
        self.members[client] = clientaddress

    def removeClient(self, client, channel):
        print('Closed connection from: {}'.format(self.clientList[client]['msgData'].decode('utf-8')))

        # Remove from list for socket.socket()
        self.socketList.remove(client)

        # Remove from our list of users
        del self.clientList[client]

        self.channels[channel].remove_member(self.usernames[client])

    def executeCommands(self, message, user) -> bool:
        message = message.split()
        command = message[0]
        relatedData = message[1]
        command_found = False
        if command == "JOIN":
            print("------message------")
            print(command)
            self.joinChannel(relatedData, user)
            command_found = True
        elif command == "PING":
            command_found = True
            pass
        elif command == "PONG":
            command_found = True
            pass
        elif command.find("PRIVMSG"):
            channel = message.split('PRIVMSG', 1)[1].split(' ', 1)[1].split(' ', 1)[0]
            print(channel)
            PRIVMSG = message.split('PRIVMSG', 1)[1].split(':', 1)[1]
            print(PRIVMSG)

        return command_found

    # TODO this has to be made so that (if a channel doesn't exist) the channel is created,
    #   if it does already exist, the client has to be entered into it.
    def joinChannel(self, channel, client_socket):
        server_channel = self.channels[channel]
        server_channel.addMember(self.usernames_returns_username[client_socket], client_socket)


# from https://github.com/jrosdahl/miniircd/blob/master/miniircd lines 1053-1060
_ircstring_translation = bytes.maketrans(
    (string.ascii_lowercase.upper() + "[]\\^").encode(),
    (string.ascii_lowercase + "{}|~").encode(),
)


def irc_lower(s: bytes) -> bytes:
    return s.translate(_ircstring_translation)
