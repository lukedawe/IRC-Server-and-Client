# Netflix type system demo - FakeFlix
import csv
import hashlib
import ipaddress
import sys
from Server import Server


def main():
    menu()


def menu():
    choice = input("""
                      A: Create server
                      B: Add client
                      C: Test server
                      Q: Quit

                      Please enter your choice: """)

    if choice == "A" or choice == "a":
        createServer()
    elif choice == "B" or choice == "b":
        addClient()
    elif choice == "C" or choice == "c":
        testServer()
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
    address = input("Please enter the IP address for the server")
    try:
        ipv6 = ipaddress.ip_address(address)
    except:
        ipv6 = ""

    server = Server(port, password, channel, ipv6)


def addClient():
    pass


def testServer():
    pass


# the program is initiated, so to speak, here
main()
