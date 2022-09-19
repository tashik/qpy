import socket
from qpy.event_manager import EVENT_ACCOUNT, EVENT_BAR, EVENT_CONTRACT, EVENT_ORDER, EVENT_TICK, EVENT_TRADE, EventManager, Event

from qpy.quik_bridge import QuikBridge, QuikConnectorTest

class QuikConnectorTest(object):
    def __init__(self, bridge: QuikBridge):
        self.qbridge = bridge
        self.event_manager = self.qbrige.event_manager
        self.msgId = 0
        self.sayHelloMsgId = None
        self.msgWasSent = False
        self.clsListReqId = None
        self.clsList = None
        self.createDsReqId = None
        self.ds = None
        self.setUpdCBReqId = None
        self.updCBInstalled = False
        self.updCnt = 0
        self.closeDsMsgId = None
        self.register_handlers()

    def register_handlers(self):
        self.event_manager.register(EVENT_ACCOUNT, self.ansArrived)
        self.event_manager.register(EVENT_CONTRACT, self.ansArrived)
        self.event_manager.register(EVENT_BAR, self.barArrived)
        self.event_manager.register(EVENT_TICK, self.reqArrived)
        self.event_manager.register(EVENT_TRADE, self.ansArrived)
        self.event_manager.register(EVENT_ORDER, self.ansArrived)

    def nextStep(self):
        if not self.msgWasSent:
            self.sayHello()
            self.msgWasSent = True
        else:
            if self.clsList is None:
                if self.clsListReqId is None:
                    self.getClassesList()
            elif self.ds is None:
                if self.createDsReqId is None:
                    self.createDs()
            elif not self.updCBInstalled:
                self.setDsUpdateCallback()
            elif self.updCnt >= 10:
                if self.closeDsMsgId is None:
                    self.closeDs()

    def barArrived(self, event: Event):
        pass


    def reqArrived(self, id, data):
        super().reqArrived(id, data)
        if data["method"] == 'invoke':
            if data["function"] == 'sberUpdated':
                idx = data["arguments"][0]
                ans = {"method": "return", "result": self.sberUpdated(idx)}
                self.sendAns(id, ans)


    def ansArrived(self, id, data):
        super().ansArrived(id, data)
        if id == self.clsListReqId:
            self.clsList = data['result'][0].split(",")
            self.clsList = list(filter(None, self.clsList))
            print("Received", len(self.clsList), "classes")
        elif id == self.createDsReqId:
            self.ds = data['result'][0]
        elif id == self.closeDsMsgId:
            self.end()
        elif id == self.sayHelloMsgId:
            print("hello sent")
        elif id == self.setUpdCBReqId:
            print("update handler installed")
        else:
            self.updCnt += 1
            # self.end()

    def sayHello(self):
        self.msgId += 1
        self.sendReq(self.msgId, {"method": "invoke", "function": "PrintDbgStr", "arguments": ["Hello from python!"]})
        # self.sendReq(self.msgId, {"method": "invoke", "function": "message", "arguments": ["Hello from python!", 1]})
        self.sayHelloMsgId = self.msgId

    def getClassesList(self):
        self.msgId += 1
        self.sendReq(self.msgId, {"method": "invoke", "function": "getClassesList", "arguments": []})
        self.clsListReqId = self.msgId

    def createDs(self):
        self.msgId += 1
        self.sendReq(self.msgId, {"method": "invoke", "function": "CreateDataSource", "arguments": ["TQBR", "SBER", 5]})
        self.createDsReqId = self.msgId

    def setDsUpdateCallback(self):
        self.msgId += 1
        self.sendReq(self.msgId, {"method": "invoke", "object": self.ds, "function": "SetUpdateCallback", "arguments": [{"type": "callable", "function": "sberUpdated"}]})
        self.setUpdCBReqId = self.msgId
        self.updCBInstalled = True

    def closeDs(self):
        self.msgId += 1
        self.sendReq(self.msgId, {"method": "invoke", "object": self.ds, "function": "Close", "arguments": []})
        self.closeDsMsgId = self.msgId

    def sberUpdated(self, index):
        print("sberUpdated:", index)
        req = {"method": "invoke", "object": self.ds, "function": "C", "arguments": [index]}
        self.msgId += 1
        self.sendReq(self.msgId, req)
        return True

if __name__ == "main":
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    # Connect the socket to the port where the server is listening
    server_address = ('localhost', 57777)
    # server_address = ('10.211.55.21', 62787)
    # server_address = ('37.193.88.181', 57578)
    print('connecting to %s port %d' % server_address)
    sock.connect(server_address)

    event_man = EventManager()
    bridge = QuikBridge(sock, event_man)
    tester = QuikConnectorTest(bridge)

    sock.setblocking(0)
    while not tester.weEnded:
        rrRes = tester.readyRead()
        if not rrRes:
            tester.nextStep()

    print("finished")