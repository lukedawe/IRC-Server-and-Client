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
                      B: Add bot
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
    server = Server()


def addClient():
    pass


def testServer():
    pass


# the program is initiated, so to speak, here
main()
