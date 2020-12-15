import socket
import sys
import time

server="chat.freenode.net"
channel="##testchanneloneagz"
botnick="TestingBestingResting"
text=""
#
irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
irc.connect((server, 6667))
irc.send(bytes("USER " + botnick + " " + botnick + " " + botnick + " " + botnick + "\n", "UTF-8"))
time.sleep(1)
irc.send(bytes("NICK " + botnick + "\n", "UTF-8"))
time.sleep(1)
irc.send(bytes("JOIN " + channel + "\n", "UTF-8"))  # join the chan

while 1:

    try:
        text = irc.recv(2040)
        print(text)
        print("\n")
    except Exception:
        pass
    if text.find(bytes('PING','UTF-8')) != -1:
        # Takes second element on Ping appends it to pong so it is correct to server
        irc.send(bytes('PONG ' + text.split()[1].decode("UTF-8")  + '\r\n', "UTF-8"))

    if text.find(bytes(":!josh", 'UTF-8'))!= -1:

        irc.send(bytes("PRIVMSG "+channel+" :Yeah that guy is gay!\r\n",'UTF-8'))
