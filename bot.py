# Import
import socket
import sys
import random
import time
import string

# Create basic variables to access server
server = "chat.freenode.net"
channel = "##testchanneloneagz"
botnick = "Gavin"
text = ""


# This function will take a random line from the fact.txt file and return it.
def random_line(fname):
    line = random.choice(open(fname, 'r', encoding='cp850').readlines())
    print(line)
    return line


irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


# This code connects the bot to the server and checks for errors in case of failure.
try:
    irc.connect((server, 6667))
except socket.error:
    print('Error connecting to IRC server')
    sys.exit(1)
irc.send(bytes("USER " + botnick + " " + botnick + " " + botnick + " " + botnick + "\n", "UTF-8"))
time.sleep(1)
irc.send(bytes("NICK " + botnick + "\n", "UTF-8"))
time.sleep(1)
irc.send(bytes("JOIN " + channel + "\n", "UTF-8"))  # join the channel

parts = ""

# This code will...
while 1:
    try:
        text = irc.recv(2040)
        print(text)
        textclean = text.strip(str.encode('\n\r'))
        parts = textclean.split('!')
        print("\n")

    except Exception:
        pass
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)

    if text.find(bytes('PING', 'UTF-8')) != -1:
        # Takes second element on Ping appends it to pong so it is correct to server
        irc.send(bytes('PONG ' + text.split()[1].decode("UTF-8") + '\r\n', "UTF-8"))

    if text.find(bytes(":!hello", 'UTF-8')) != -1:
        irc.send(bytes("PRIVMSG "+channel+" :Hello, the time is " + current_time + "!\r\n", 'UTF-8'))

    if text.find(bytes(":!fact", 'UTF-8')) != -1:
        source = bytes(parts[0]).strip(bytes('!','UTF-8'))
        irc.send(bytes("PRIVMSG"+ str(source) +" "+ channel + " :" + random_line("facts.txt") + "\r\n", 'UTF-8'))



