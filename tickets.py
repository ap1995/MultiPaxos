from socket import *
from _thread import *
import json
import shutil
import random
import time
import sys

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
        self.BallotNum = BallotNum(0,self.port)
        self.AcceptNum = BallotNum(0,0)
        self.AcceptVal = 0
        self.numOfAcks = 0
        self.accepts = 0
        self.leaderport = 4003
        self.leaderIsAlive = True
        self.electionInProgress = False
        self.log = []
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
        # else:
        #     start_new_thread(self.timer, ())

        while True:
            pass

    def receiveMessages(self, conn, addr):
        msg = conn.recv(1024).decode()
        print(msg)

        if "Leader" in msg:
            self.leaderport = int(msg.split()[-1])
            self.electionInProgress = False
            mesg = "Election ended"
            self.sendToAll(mesg)

        if "prepare" in msg:
            num1 = int(msg.split()[1])
            sendToPort = int(msg.split()[-1])
            if num1 > self.BallotNum.num or (num1 == self.BallotNum.num and sendToPort > int(self.BallotNum.ID)):
                self.BallotNum.num = num1
                message = "ack" + str(self.BallotNum.num) + " " + str(self.AcceptNum.num) + " " + str(self.AcceptNum.ID) + str(self.AcceptVal)
                self.sendMessage(sendToPort, message)

        if "ack" in msg:
            num1 = int(msg.split()[1])
            receivedVal = int(msg.split()[-1])
            self.numOfAcks += 1
            # majority = math.ceil((len(CLIENTS) + 2) / 2)
            if receivedVal > self.AcceptVal:
                self.AcceptVal = receivedVal
            if self.numOfAcks == 2:
                leaderport = self.leaderport
                msg = "Leader" + str(leaderport)
                      # str(self.BallotNum.num) + " " + str(self.AcceptVal)
                self.sendToAll(msg)

        if "accepted " in msg:
            ballNum = int(msg.split()[1])
            v = int(msg.split()[-1])
            self.acceptances[self.accepts] = [ballNum, v]
            print("Acceptances: ")
            print(self.acceptances)
            self.accepts += 1
            if (self.accepts == 2):  # n-1
                message = "Add to log " + str(v) # Commit to log
                print(message)
                self.log.append(v)
                self.sendToAll(message)
                self.acceptances = [[0 for x in range(2)] for y in range(2)]
                self.accepts =0

        if "accept " in msg: #I am not a leader
            num = int(msg.split()[1])
            val = int(msg.split()[2])
            senderID = msg.split()[-2]
            senderport = int(msg.split()[-1])
            # print("My BallotNum when accept message received" + str(self.BallotNum.num))
            if num > self.BallotNum.num or (num == self.BallotNum.num and senderport > int(self.BallotNum.ID)):
                self.AcceptNum.num = num
                self.AcceptNum.ID = senderID
                self.AcceptVal = val # Accept Proposal
            message = "accepted "+ str(self.AcceptNum.num) + " "+ str(self.AcceptNum.ID) + " "+ str(self.AcceptVal) #####?????#####
            self.sendMessage(senderport, message)

        if "Value received" in msg: #By leader
            valReceived = msg.split()[-2]
            self.sendAcceptRequests(valReceived)

        if "heartbeat" in msg:
            self.leaderIsAlive = True
            self.timer()

        if "Election " in msg:
            electionStatus = msg.split()[-1]
            if electionStatus == "begun":
                self.electionInProgress = True
            if electionStatus == "ended":
                self.electionInProgress = False

        if "Add to log" in msg:
            val = int(msg.split()[-1])
            self.log.append(val)
            print("Current log is: ")
            print(self.log)

    def leaderCheck(self): #Check if Leader is alive
        if self.leaderIsAlive == False:
            if self.electionInProgress == False:
                self.startElection()

    def startElection(self): # Leader down, new election begun
        message = "Election begun"
        self.electionInProgress =True
        self.sendToAll(message)
        time.sleep(5)
        # self.leaderport = 4003
        self.BallotNum.num += 1
        message = "prepare " + str(self.BallotNum.num) + " " + str(self.BallotNum.ID)
        self.sendToAll(message)

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
                elif self.leaderIsAlive == True :
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
        timetosleep = 0.5 + (self.processID*0.1)
        time.sleep(timetosleep) # Sleep for 0.5s + processID*0.1
        self.leaderCheck()

    def sendHeartbeat(self):
        while(1):
            time.sleep(0.5)
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
                    pass
                    # print(str(portnum) + " is dead")

    def closeSocket(self):
        self.s.close()

######## MAIN #########

with open('config.json') as configfile:
    configdata = json.load(configfile)

delay = configdata["delay"]
ID = str(sys.argv[1])
tickets = configdata["tickets"]
c = Tickets(ID)
