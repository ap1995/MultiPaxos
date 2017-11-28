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
        self.ID = ID #C1
        self.port = configdata["kiosks"][ID][1]
        self.processID = int(self.port) - 4000 #1
        self.hostname = gethostname()
        self.BallotNum = BallotNum(0,ID)
        self.AcceptNum = BallotNum(0,0)
        self.AcceptVal = 0
        self.numOfAcks = 0
        self.accepts = 0
        self.leaderport = 4003
        self.leaderIsAlive = False
        self.electionInProgress = False
        w, h = 5, 2 # 4, n-1
        self.acks = [[0 for x in range(w)] for y in range(h)]
        self.acceptances = [[0 for x in range(2)] for y in range(2)] #n-1 rows
        self.s = socket(AF_INET, SOCK_STREAM)
        time.sleep(5)
        self.leaderCheck()
        start_new_thread(self.startListening, ())
        start_new_thread(self.awaitInput, ()) # If leader send Heartbeat else timer
        if self.leaderport == int(self.port):
            start_new_thread(self.sendHeartbeat(), ())
        else:
            start_new_thread(self.timer, ())

        while True:
            pass

    def receiveMessages(self, conn, addr):
        msg = conn.recv(1024).decode()
        print(msg)

        if "Leader" in msg:
            self.leaderport = int(msg.split()[-1])

        if "accepted " in msg:
            ballNum = int(msg.split()[1])
            v = int(msg.split()[-1])
            self.acceptances[self.accepts] = [ballNum, v]
            print("Acceptances: ")
            print(self.acceptances)
            self.accepts += 1
            if (self.accepts == 2):  # n-1
                print("Add to log")# Commit to log
                self.acceptances = [[0 for x in range(2)] for y in range(2)]
                self.accepts =0

        if "accept " in msg: #I am not a leader
            num = int(msg.split()[1])
            val = int(msg.split()[2])
            senderID = msg.split()[-2]
            senderport = int(msg.split()[-1])
            # print("My BallotNum when accept message received" + str(self.BallotNum.num))
            if(num>=self.BallotNum.num):
                self.AcceptNum.num = num
                self.AcceptNum.ID = senderID
                self.AcceptVal = val # Accept Proposal
            message = "accepted "+ str(self.AcceptNum.num) + " "+ str(self.AcceptNum.ID) + " "+ str(self.AcceptVal) #####?????#####
            self.sendMessage(senderport, message)

        if "Value received" in msg:
            valReceived = msg.split()[-2]
            self.sendAcceptRequests(valReceived)

        if "heartbeat" in msg:
            self.leaderIsAlive = True

        if "Election " in msg:
            electionStatus = msg.split()[-1]
            if electionStatus == "begun":
                self.electionInProgress = True
            if electionStatus == "ended":
                self.electionInProgress = False

    def leaderCheck(self): #Check if Leader is alive
        if self.leaderIsAlive == False:
            if self.electionInProgress == False:
                self.startElection()

    def startElection(self): # Leader down, new election begun
        message = "Election begun"
        self.electionInProgress =True
        self.sendToAll(message)
        time.sleep(5)
        self.leaderport = 4003
        # Ask everyone greater than you if they are alive
        self.electionInProgress = False
        msg = "Election ended"
        self.sendToAll(msg)

    def sendAcceptRequests(self, val):
        initialValue = self.AcceptVal
        newVal = val
        self.BallotNum.num+=1
        message = "accept "+ str(self.BallotNum.num) + " "+ str(newVal) + " coming from "+ str(self.ID) + " " + str(self.port)
        self.sendToAll(message)

    def awaitInput(self):
        while True:
            message = input('Enter number of tickets you wish to buy ')
            val = int(message)
            try:
                  # change to if 'Buy 2' or 'show'
                if (self.leaderport == self.port):
                    self.sendAcceptRequests(val)
                else:
                    msg = "Value received " + str(val) + " " + str(self.port)
                    self.sendMessage(self.leaderport, msg)
            except ValueError:
                print("Invalid Input")

    def startListening(self):
        # Add my details to configdata
        with open('live.json', 'a') as livefile:
            json.dump({ID:configdata["kiosks"][ID]}, livefile, ensure_ascii=False)
        # print(livefile)
        try:
            self.s.bind((self.hostname, int(self.port)))
            self.s.listen(5)
            print("server started on port " + str(self.port))
            while True:
                c, addr = self.s.accept()
                conn = c
                # print('Got connection from')
                # print(addr)
                start_new_thread(self.receiveMessages, (conn, addr))  # connection dictionary
        except(gaierror):
            print('There was an error making a connection')
            self.s.close()
            sys.exit()

    def sendMessage(self, port, message):
        rSocket = socket(AF_INET, SOCK_STREAM)
        rSocket.connect((gethostname(), int(port)))
        # print(message)
        rSocket.send(message.encode())
        rSocket.close()

    def timer(self):
        timetosleep = 1 + (self.processID*0.1)
        time.sleep(timetosleep) # Sleep for 1s + processID*0.1
        self.leaderCheck()

    def sendHeartbeat(self):
        while(1):
            for i in range(0,499):
                pass
            msg = "heartbeat"
            self.sendToAll(msg)

    # To send messages to everyone
    def sendToAll(self, message):
        portnum = 0
        for i in configdata["kiosks"]:
            if (configdata["kiosks"][i][1] == self.port):  ## To not send to yourself
                continue
            else:
                try:
                    cSocket = socket(AF_INET, SOCK_STREAM)
                    ip, port = configdata["kiosks"][i][0], configdata["kiosks"][i][1]
                    portnum = port
                    port = int(port)
                    cSocket.connect((gethostname(), port))
                    print('Connected to port number ' + configdata["kiosks"][i][1])
                    cSocket.send(message.encode())
                    print('Message sent to customer at port ' + str(port))
                    cSocket.close()
                except ConnectionError:
                    print(str(portnum) + " is dead")

    def closeSocket(self):
        self.s.close()

######## MAIN #########

with open('config.json') as configfile:
    configdata = json.load(configfile)

delay = configdata["delay"]
ID = str(sys.argv[1])
tickets = configdata["tickets"]
c = Tickets(ID)
