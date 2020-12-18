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
        self.channels: Dict[string, Channel] = {}  # key: irc_lower(channelname)
        self.clients: Dict[Socket, Client] = {}
        self.usernames: Dict[string, Socket] = {}  # username connected to socket
        self.nicknames: Dict[string, string] = {}  # nickname connected to username
        # self.threads: Dict[bytes, Channel] = {}
        self.clientList = {}

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

        print(f'Listening for connections on {self.ipv6}:{self.ports[0]}...')
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
        cap = self.reveiveMessageMk3(client_socket)
        user = self.reveiveMessageMk3(client_socket)

        if not (cap and user):
            return False
        else:

            userinfo = user.split()
            nickname = userinfo[1]
            username = userinfo[3]

            self.usernames[username] = client_socket
            self.nicknames[nickname] = username

            print("nick: " + nickname)
            print("username: " + username)

            # print("message data: " + user['msgData'].decode('utf-8'))
            address = str(client_address[0])
            port = int(client_address[1])

            print(port)
            print(address)

            # TODO we cannot bind the address and the port for some reason :(
            client_socket.bind((address, port))
            client_socket.listen()

            # Add accepted socket to select.select() list
            self.socketList.append(client_socket)

            # Also save username and username header
            self.clientList[client_socket] = user

            textToSend = "001 " + nickname + " :Welcome, " + nickname + " to our shitty IRC server, ya filthy cunt"
            textToSend = "CAP * LS :"
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

            received = self.reveiveMessageMk3(client_socket)

            print(received)

            return True

    def receiveMessage(self, clientSocket):
        try:
            messageHeader = clientSocket.recv(10)
            print("message header: " + messageHeader)
            if not len(messageHeader):
                return False

            messageLength = int(messageHeader.decode('utf-8').strip())
            return {'header': messageHeader, 'msgData': clientSocket.recv(messageLength)}

        except:
            return False

    def receiveMessageMk2(self, clientSocket):
        chunks = []
        bytes_recd = 0
        while bytes_recd < MSGLEN:
            chunk = clientSocket.recv(min(MSGLEN - bytes_recd, MSGLEN))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return b''.join(chunks)

    def reveiveMessageMk3(self, clientSocket):
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
                    message = self.reveiveMessageMk3(notified_socket)
                    print(message)

                    # If False, client disconnected, cleanup
                    if message is False:
                        # Remove from list for socket.socket()
                        self.removeClient(notified_socket)

                        continue

                    # Get user by notified socket, so we will know who sent the message
                    user = self.clientList[notified_socket]

                    print(
                        f'Received message from {user["msgData"].decode("utf-8")}: {message["msgData"].decode("utf-8")}')

                    # Iterate over connected clients and broadcast message
                    for client_socket in self.clientList:

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

            # It's not really necessary to have this, but will handle some socket exceptions just in case
            for notified_socket in exception_sockets:
                # Remove from list for socket.socket()
                self.socketList.pop(notified_socket)

                # Remove from our list of users
                del self.clientList[notified_socket]

    def addMember(self, client, clientaddress) -> None:
        self.members[client] = clientaddress

    def removeClient(self, client):
        print('Closed connection from: {}'.format(self.clientList[client]['msgData'].decode('utf-8')))

        # Remove from list for socket.socket()
        self.socketList.remove(client)

        # Remove from our list of users
        del self.clientList[client]


# from https://github.com/jrosdahl/miniircd/blob/master/miniircd lines 1053-1060
_ircstring_translation = bytes.maketrans(
    (string.ascii_lowercase.upper() + "[]\\^").encode(),
    (string.ascii_lowercase + "{}|~").encode(),
)


def irc_lower(s: bytes) -> bytes:
    return s.translate(_ircstring_translation)
