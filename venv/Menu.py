import sys
import threading

from Server import Server
from bot import Bot

IPV6_MESSAGE = "Please enter the port you wish to use or press enter to accept default (default is 6667)"
PORT_MESSAGE = "Please enter the ipv6 you wish to use or press enter to accept default (default is fc00:1337::17)"
THREADING_ERROR = "Threading error occurred, don't create two of the same thread at once!"


def main():
    menu()


def menu():

    choice = input("""
                      A: Create server
                      B: Add bot (make sure to run the server first)
                      C: Create a bot and a server as once
                      Q: Quit

                      Please enter your choice: """)

    if choice == "A" or choice == "a":
        print("Creating server")
        try:
            port = input(PORT_MESSAGE)
            ipv6 = input(IPV6_MESSAGE)
            x = threading.Thread(target=create_server, args=(port, ipv6))
            x.start()
        except:
            print(THREADING_ERROR)
            menu()
    elif choice == "B" or choice == "b":
        print("Adding bot to the server")
        try:
            y = threading.Thread(target=create_bot, args=())
            y.start()
        except:
            print(THREADING_ERROR)
            menu()
    elif choice == "C" or choice == "c":
        print("Creating a server and a bot")
        try:
            port = input(PORT_MESSAGE)
            ipv6 = input(IPV6_MESSAGE)
            x = threading.Thread(target=create_server, args=(port, ipv6))
            x.start()
            y = threading.Thread(target=create_bot, args=())
            y.start()
        except:
            print(THREADING_ERROR)
            menu()
    elif choice == "Q" or choice == "q":
        sys.exit()
    else:
        print("You must only select either A or B")
        print("Please try again")
        menu()


def create_server(port, ipv6):
    if port and ipv6:
        print("running this")
        Server(port, ipv6)
    elif ipv6:
        Server(None, ipv6)
    else:
        print("Running with no params")
        Server()


def create_bot():
    Bot()


# the program is initiated, so to speak, here
main()
