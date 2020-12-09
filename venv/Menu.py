# Netflix type system demo - FakeFlix
import csv
import hashlib
import sys
import Server


def main():
    menu()


def menu():

    choice = input("""
                      A: Create Server
                      B: Add client
                      Q: Quit

                      Please enter your choice: """)

    if choice == "A" or choice == "a":
        createServer()
    elif choice == "B" or choice == "b":
        addClient()
    elif choice == "Q" or choice == "q":
        sys.exit
    else:
        print("You must only select either A or B")
        print("Please try again")
        menu()


def createServer():
    port = input("Please enter the port for the server")
    password = input("Please enter the password for the server")
    password = hashlib.sha224(str.encode(password)).hexdigest()
    channel = input("Please enter the channel for the server")
    ipv6 = input("Please enter the IP address for the server")
    listen = input("Please enter the listen for the server")

    server = Server(port,password,channel,ipv6,listen)

def addClient():
    pass


# the program is initiated, so to speak, here
main()