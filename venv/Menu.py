import sys
import threading

from Server import Server
from bot import Bot


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
            port = input("Please enter the port you wish to use (default is 6667)")
            ipv6 = input("Please enter the ipv6 you wish to use (default is fc00:1337::17)")
            x = threading.Thread(target=create_server, args=(port, ipv6))
            x.start()
        except:
            print("Threading error occurred, don't create two servers at once!")
            menu()
    elif choice == "B" or choice == "b":
        print("Adding bot to the server")
        try:
            y = threading.Thread(target=create_bot, args=())
            y.start()
        except:
            print("Threading error occurred, don't create two bots at once!")
            menu()
    elif choice == "C" or choice == "c":
        print("Creating a server and a bot")
        try:
            port = input("Please enter the port you wish to use (default is 6667)")
            ipv6 = input("Please enter the ipv6 you wish to use (default is fc00:1337::17)")
            x = threading.Thread(target=create_server, args=(port, ipv6))
            x.start()
            y = threading.Thread(target=create_bot, args=())
            y.start()
        except:
            print("Threading error occurred, don't create two bots at once!")
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
