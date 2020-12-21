import sys
import threading

from Server import Server
from bot import Bot


def main():
    menu()


def menu():
    while True:
        choice = input("""
                          A: Create server
                          B: Add bot
                          C: Test server
                          Q: Quit
    
                          Please enter your choice: """)

        if choice == "A" or choice == "a":
            x = threading.Thread(target=create_server, args=())
            x.start()
        elif choice == "B" or choice == "b":
            y = threading.Thread(target=create_bot, args=())
            y.start()
        elif choice == "C" or choice == "c":
            test_server()
        elif choice == "Q" or choice == "q":
            sys.exit
        else:
            print("You must only select either A or B")
            print("Please try again")
            menu()


def create_server():
    Server()


def create_bot():
    Bot()


def test_server():
    pass


# the program is initiated, so to speak, here
main()
