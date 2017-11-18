from socket import *
from _thread import *
import json
import shutil
import random
import time
import sys
# import ballot

class BallotNum:
    def __init__(self, num, ID):
        self.num = num
        self.ID = ID

class Tickets:
    def __init__(self, ID):
        print("System running: " + ID)
        self.ID = ID
        self.port = configdata["kiosks"][ID][1]
        self.processID = int(self.port) - 4000
        self.hostname = gethostname()
        self.BallotNum = BallotNum(0,0)
        self.AcceptNum = BallotNum(0,0)
        self.AcceptVal = 0
        self.numOfAcks = 0
        self.accepts = 0
        w, h = 4, 5
        self.acks = [[0 for x in range(w)] for y in range(h)]
        self.acceptances = [[0 for x in range(w)] for y in range(h)]
        self.s = socket(AF_INET, SOCK_STREAM)
        start_new_thread(self.startListening, ())
        while True:
            pass

    def receiveMessages(self, conn, addr):
        msg = conn.recv(1024).decode()
        print(msg)

        if "prepare" in msg:
            receivedNum = int(msg.split()[1])
            # receivedID = int(msg.split()[2])
            leaderport = int(msg.split()[-1])
            if(receivedNum > self.BallotNum.num):
                self.BallotNum.num = receivedNum
                message = "ack "+ str(receivedNum)+ str(self.AcceptNum) + " " + str(self.AcceptVal) + " "+ str(self.port)
                self.sendMessage(leaderport, message)

        if "accept " in msg: #I am not a leader
            num = msg.split()[1]
            val = msg.split()[2]
            leaderID = msg.split()[-2]
            leaderport = msg.split()[-1]
            if(num>self.BallotNum.num):
                self.AcceptNum.num = num
                self.AcceptNum.ID = leaderID
                self.AcceptVal = val # Accept Proposal
            message = "accepted "+ str(self.AcceptNum.num) + " "+ str(self.AcceptNum.ID) + " "+ str(self.AcceptVal) #####?????#####
            self.sendMessage(leaderport, message)

        if "ack" in msg:
            bNum = msg.split()[1]
            aNum = msg.split()[2]
            val = msg.split()[3]
            port = msg.split()[-1]
            self.acks[self.numOfAcks] = [bNum, aNum, val, port]
            self.numOfAcks+=1
            if(self.numOfAcks ==3):
                self.checkVals(self.acks)
    
        # if "accepted" in msg:
        #     b = msg.split()[1]
        #     v = msg.split()[-1]
        #     self.acceptances[self.accepts] = [b, v]
        #     self.accepts+=1
        #     if(self.accepts ==3):
        #         self.informDecision()

    def awaitInput(self):
        while True:
            message = input('Enter number of tickets you wish to buy ')
            try:
                val = int(message)
            except ValueError:
                print("Invalid Input")
            self.sendPrepare(self.ID)
            
    # def informDecision(self):
    #     message = "decided "
    #     self.sendToAll(message)

    def checkVals(self, acks):
        initialValue = self.AcceptVal
        newVal = initialValue
        num = self.BallotNum.num
        for i in range(3):
            if acks[i][2] > initialValue:
                num = acks[i][0]
                newVal = acks[i][2]
        self.BallotNum.num = num
        message = "accept "+ str(num) + " "+ str(newVal) + " coming from "+ str(self.ID) + " " + str(self.port)
        self.sendToAll(message)

    def sendPrepare(self, ID):
        self.BallotNum.num +=1
        self.BallotNum.ID = ID
        message = "prepare " + str(self.BallotNum.num) + " "+ str(self.BallotNum.ID) + " from "+str(self.port)
        self.sendToAll(message)

    def startListening(self):
        # Add my details to configdata
        try:
            self.s.bind((self.hostname, int(self.port)))
            self.s.listen(3)
            print("server started on port " + str(self.port))
            while True:
                c, addr = self.s.accept()
                conn = c
                print('Got connection from')
                print(addr)
                start_new_thread(self.receiveMessages, (conn, addr))  # connection dictionary
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
# runningConfig = dict()
ID = sys.argv[1]
tickets = configdata["tickets"]
c = Tickets(ID)
