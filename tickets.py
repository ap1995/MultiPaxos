from socket import *
from _thread import *
import json
import shutil
import random
import time
import sys

class Tickets:
    def __init__(self, ID):
        print("System running: " + ID)
        self.ID = ID
        self.port = configdata["kiosks"][ID][1]
        self.processID = int(self.port) - 4000
        self.hostname = gethostname()
        self.s = socket(AF_INET, SOCK_STREAM)

        while True:
            pass

    def awaitInput(self):

        while True:
            message = input('Enter number of tickets you wish to buy ')
            try:
                val = int(message)
            except ValueError:
                print("Invalid Input")

            def startListening(self):
                try:
                    self.s.bind((self.hostname, int(self.port)))
                    self.s.listen(3)
                    print("server started on port " + str(self.port))
                    while True:
                        c, addr = self.s.accept()
                        conn = c
                        print('Got connection from')
                        print(addr)
                        # start_new_thread(self.receiveMessages, (conn, addr))  # connection dictionary
                except(gaierror):
                    print('There was an error making a connection')
                    self.s.close()
                    sys.exit()

            def sendMessage(self, port, message):
                rSocket = socket(AF_INET, SOCK_STREAM)
                rSocket.connect((gethostname(), int(port)))
                print(message)
                rSocket.send(message.encode())
                rSocket.close()

            # To send messages to everyone
            def sendToAll(self, message):
                for i in configdata["kiosks"]:
                    if (configdata["kiosks"][i][1] == self.port):  ## To not send to yourself
                        continue
                    else:
                        cSocket = socket(AF_INET, SOCK_STREAM)
                        ip, port = configdata["kiosks"][i][0], configdata["kiosks"][i][1]
                        port = int(port)
                        cSocket.connect((gethostname(), port))
                        print('Connected to port number ' + configdata["kiosks"][i][1])
                        cSocket.send(message.encode())
                        print('Message sent to customer at port ' + str(port))
                        cSocket.close()

            def closeSocket(self):
                self.s.close()


######## MAIN #########

with open('config.json') as configfile:
    configdata = json.load(configfile)

delay = configdata["delay"]

ID = sys.argv[1]
tickets = configdata["tickets"]
c = Tickets(ID)
