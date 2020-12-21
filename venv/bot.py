# Import required libraries: allows us to use built-in functions
import os
import socket
import sys
import random
import time


# Create basic variables to access server
# Create a socket instance. This facilitates a bots connection to the server


class Bot:

    def __init__(self):
        # self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.irc = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        # self.server = "chat.freenode.net"
        self.server = "::1"
        # self.channel = "##testchanneloneagz"
        self.channel = "#test"
        self.botnick = "Ginger"
        self.run_bot()

    # This function will take a random line from the facts.txt file and return it.
    def random_line(self, fname) -> str:
        here = os.path.dirname(os.path.abspath(__file__))
        print(here)
        try:
            line = random.choice(open(fname, 'r', encoding='cp850').readlines())
            return line

        except IOError:
            return "Facts file not found"

    # Connects the bot to the server and checks for errors in case of failure.
    def connect_to_server(self):
        try:
            # irc.connect((server, 6667, 0, 0))
            self.irc.connect((self.server, 6667))
        except socket.error:
            print('Error connecting to IRC server')
            sys.exit(1)

        # Join the desired server and channel with the desired nickname (botnick)
        self.irc.send(bytes("NICK " + self.botnick + "\n", "UTF-8"))
        time.sleep(1)
        self.irc.send(bytes("USER " + self.botnick + " " + self.botnick + " " + self.botnick + " " + self.botnick + "\n"
                            , "UTF-8"))
        time.sleep(1)
        self.irc.send(bytes("JOIN " + self.channel + "\n", "UTF-8"))

    # gets the name of users in channel
    def get_names(self) -> list:
        time.sleep(0.5)
        self.irc.send(bytes('NAMES ' + self.channel + '\r\n', "UTF-8"))
        getnamelist = self.irc.recv(2048).decode("UTF-8")
        namelist = getnamelist.split(self.channel, 1)[1].split(':', 1)[1].split('\r\n', 1)[0].split(' ')
        return namelist

    # gets the current time
    def get_time(self) -> str:
        current_local_time = time.localtime()
        current_time = time.strftime("%H:%M:%S", current_local_time)
        return current_time

    # Takes second element on Ping appends it to pong so it is correct to server
    def ping(self, append_to_ping):
        self.irc.send(bytes('PONG ' + append_to_ping + '\r\n', "UTF-8"))

    # runs bot
    def run_bot(self):
        ran = False
        self.connect_to_server()
        text = ""
        while 1:
            # Constantly try to read information in from the socket
            try:
                text = self.irc.recv(2048).decode("UTF-8")
                print(text)
            except:
                pass

            name = text.split('!', 1)[0][1:]

            # If someone sends a message in the channel or private message
            if text.find("PRIVMSG") != -1:
                chat = text.split('PRIVMSG', 1)[1].split(' ', 1)[1].split(' ', 1)[0]
                message = text.split('PRIVMSG', 1)[1].split(':', 1)[1]
                print(repr(message))

                # Hello command - gives time
                if message == '!hello\r\n' and self.botnick != chat:
                    localtime = self.get_time()
                    self.irc.send(bytes("PRIVMSG " + chat + " :Hello, the time is " + localtime + "!\r\n", 'UTF-8'))

                # Use 'NAMES' command to get names of all channel users choose a random user then slap them
                if message == '!slap\r\n' and self.botnick != chat:
                    slapee = random.choice(self.get_names())
                    print(self.get_names())
                    # Special case where bot chooses to slap itself
                    if slapee == self.botnick:
                        self.irc.send(
                            bytes("PRIVMSG " + chat + " :Self harm is not a joke, but here goes...\r\n", 'UTF-8'))
                    self.irc.send(
                        bytes("PRIVMSG " + chat + " :Slaps " + slapee + " around with a wet trout\r\n", 'UTF-8'))

                # If the user does '!fact' in the public channel, a fact will be private messaged to them.
                # If the user sends a private message to the bot, the bot responds with a fact
                if message == '!fact\r\n':
                    self.irc.send(bytes("PRIVMSG " + name + " :" + self.random_line("facts.txt") + "\r\n", 'UTF-8'))
                    continue
                elif chat == self.botnick:
                    self.irc.send(bytes("PRIVMSG " + name + " :" + self.random_line("facts.txt") + "\r\n", 'UTF-8'))

                # The '!user' command shows that our bot can keep track of users on the same channel
                if message == '!users\r\n' and self.botnick != chat:
                    users = self.get_names()
                    self.irc.send(bytes("PRIVMSG " + chat + " :Users are " + " ".join(users) + "\r\n", 'UTF-8'))

            # Pong the server
            if text.find('PING') != -1:
                self.ping(text.split()[1])

            # If the someone leaves it will check how many people and in if it's one person it will leave
            if text.find("QUIT") != -1 or text.find("PART") != -1:
                if len(self.get_names()) == 1:
                    print("One boy left that means i leave ")
                    self.irc.send(bytes("QUIT Bye", "UTF-8"))
                    break

            # Statement to say the bot has joined and only runs once
            if text.find("JOIN") and name == "Ginger" != 1:
                if ran != 1:
                    self.irc.send(bytes("PRIVMSG " + self.channel + " :THE GINGER BOT IS HERE" + "\r\n", 'UTF-8'))
                    ran = True