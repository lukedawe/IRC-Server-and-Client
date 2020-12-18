# Import required libraries: allows us to use built-in functions
import socket
import sys
import random
import time

# Create basic variables to access server
server = "chat.freenode.net"
channel = "##testchanneloneagz"
botnick = "Ginger"



# This function will take a random line from the fact.txt file and return it.
# It is required for the '!fact' command
def random_line(fname):
    line = random.choice(open(fname, 'r', encoding='cp850').readlines())
    return line


# Create a socket instance. This facilitates a bots connection to the server
irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


# Connects the bot to the server and checks for errors in case of failure.
def connect_to_server():
    try:
        irc.connect((server, 6667))
    except socket.error:
        print('Error connecting to IRC server')
        sys.exit(1)

    # Join the desired server and channel with the desired nickname (botnick)
    irc.send(bytes("USER " + botnick + " " + botnick + " " + botnick + " " + botnick + "\n", "UTF-8"))
    time.sleep(1)
    irc.send(bytes("NICK " + botnick + "\n", "UTF-8"))
    time.sleep(1)
    irc.send(bytes("JOIN " + channel + "\n", "UTF-8"))

    print(botnick + " is here")

def get_names():
    irc.send(bytes('NAMES ' + channel + '\r\n', "UTF-8"))
    time.sleep(1)
    getnamelist = irc.recv(2048).decode("UTF-8")
    return getnamelist.split(channel, 1)[1].split(':', 1)[1].split('\r\n', 1)[0].split(' ')


# Main method
def main():
    connect_to_server()
    # This code will run continuously
    ran = False

    while 1:
        # Constantly try to read information in from the socket

        try:
            text = irc.recv(2048).decode("UTF-8")
            print(text)
        except Exception:
            pass
        t0 = time.time()
        # If someone sends a message in the channel then take time (for !hello), get name of senders / relevant channel
        if text.find("PRIVMSG") != -1:
            t = time.localtime()
            current_time = time.strftime("%H:%M:%S", t)
            name = text.split('!', 1)[0][1:]
            chat = text.split('PRIVMSG', 1)[1].split(' ', 1)[1].split(' ', 1)[0]

            # PING/PONG to/from the server to check for timeouts
            # Takes second element on Ping appends it to pong so it is correct to server
            if text.find('PING') != -1:
                irc.send(bytes('PONG ' + text.split()[1] + '\r\n', "UTF-8"))

            # Hello command - gives time
            if text.find(":!hello") != -1:
                irc.send(bytes("PRIVMSG " + chat + " :Hello, the time is " + current_time + "!\r\n", 'UTF-8'))

            # Slap command:
            # Use 'NAMES' command to get names of all channel users. Sleep to cope with user spam
            # Use what is returned by NAMES to create a list of active users on the channel (listOfNames)
            # From this list, choose a random user and designate them the 'slapee'. Then slap them
            if text.find(":!slap") != -1:
                slapee = random.choice(get_names())
                print(get_names())
                # Special case where bot chooses to slap itself
                if slapee == botnick:
                    irc.send(bytes("PRIVMSG " + chat + " :Self harm is not a joke, but here goes...\r\n", 'UTF-8'))

                irc.send(bytes("PRIVMSG " + chat + " :Slaps " + slapee + " around with a wet trout\r\n", 'UTF-8'))

            # Fact command:
            # If the user does '!fact' in the public channel, a fact will be private messaged to them.
            # If the user sends a private message to the bot, the bot responds with a fact
            if text.find(":!fact") != -1:
                irc.send(bytes("PRIVMSG " + name + " :" + random_line("facts.txt") + "\r\n", 'UTF-8'))
                continue
            elif chat == botnick:
                irc.send(bytes("PRIVMSG " + name + " :" + random_line("facts.txt") + "\r\n", 'UTF-8'))

            if ran == 1:
                if len(get_names()) == 1:
                    irc.send(bytes("PRIVMSG " + chat + " :" + "So lonely and sad " + "\r\n", 'UTF-8'))
                else:
                    irc.send(bytes("PRIVMSG " + chat + " :" + "Ok i'm just going to leave because no one is speaking " + "\r\n", 'UTF-8'))

            ran = True

# This run the main method
if __name__ == "__main__":
    main()

# Jesse wants this ---> message = text.split('PRIVMSG', 1)[1].split(':', 1)[1]
