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
                          B: Add bot (make sure to run the server first)
                          Q: Quit
    
                          Please enter your choice: """)

        if choice == "A" or choice == "a":
            print("Creating server")
            try:
                x = threading.Thread(target=create_server, args=())
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
        elif choice == "Q" or choice == "q":
            sys.exit()
        else:
            print("You must only select either A or B")
            print("Please try again")
            menu()

def create_server():
    Server()


def create_bot():
    Bot()


# the program is initiated, so to speak, here
main()
