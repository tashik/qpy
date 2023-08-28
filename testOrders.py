import socket
from qpy.event_manager import EVENT_ORDER_UPDATE, EVENT_NEW_TRADE, EVENT_ERROR, Event

from qpy.quik_bridge import QuikBridge

from qpy.entities import TransactionEntity

class QuikConnectorTest(object):
    def __init__(self, bridge: QuikBridge, account: str):
        self.qbridge = bridge
        self.account = account
        self.msgId = 0
        self.msgWasSent = False
        self.weEnded = False
        
        self.placed_order_id = None
        self.placed_order_num = None
        self.canceled_order_id = None

        self.register_handlers()

    def on_ping(self, event: Event):
        print("hello sent")

    def on_order_update(self, event: Event):
        if self.placed_order_num is None:
            self.placed_order_num = event.data["order"]["order_num"]
        print(f'Updated order {event.data["order"]["trans_id"]} with flag {event.data["order"]["flags"]}')

    def on_new_trade(self, event: Event):
        print(f'New trade arrived {event.data["trade"]["trade_num"]} for {event.data["trade"]["seccode"]} {event.data["trade"]["qty"]}')

    def on_error(self, event: Event):
        print(f'An error occured for message with trans id {event.data["transaction"]["TRANS_ID"]}')

    def register_handlers(self):
        self.qbridge.register(EVENT_ERROR, self.on_error)
        self.qbridge.register(EVENT_ORDER_UPDATE, self.on_order_update)
        self.qbridge.register(EVENT_NEW_TRADE, self.on_new_trade)
        
    def nextStep(self):
        if not self.msgWasSent:
            self.test_say_hello()
            self.msgWasSent = True
            self.test_global_callbacks()
        else:
            if not self.placed_order_id:
                self.test_place_order()
            elif self.placed_order_num and not self.canceled_order_id:
                self.test_cancel_order()
            elif self.canceled_order_id:
                self.weEnded = True


    def test_say_hello(self):
        msg_id = self.qbridge.sayHello()
        self.sayHelloMsgId = msg_id
        self.msgWasSent = True

    def test_global_callbacks(self):
        self.qbridge.setGlobalCallback("OnTransReply")
        self.qbridge.setGlobalCallback("OnOrder")
        self.qbridge.setGlobalCallback("OnTrade")

    def test_place_order(self):
        tran = TransactionEntity(self.account, "P-TEST", "L", str(self.qbridge.indexer.get_index()), "SPBFUT", "SiU3", "NEW_ORDER", "B", "90000", "1")
        self.placed_order_id = tran.TRANS_ID
        self.qbridge.sendTransaction(tran)

    def test_cancel_order(self):
        tran = TransactionEntity(self.account, "P-TEST", "L", self.qbridge.indexer.get_index(), "SPBFUT", "SiU3", "KILL_ORDER", "B", "90090", "1", self.placed_order_num)
        self.canceled_order_id = self.placed_order_id
        self.qbridge.sendTransaction(tran)

if __name__ == "__main__":
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    # Connect the socket to the port where the server is listening
    server_address = ('localhost', 57777)
    # server_address = ('10.211.55.21', 62787)
    # server_address = ('37.193.88.181', 57578)
    print('connecting to %s port %d' % server_address)
    sock.connect(server_address)
    sock.setblocking(0)

    acc = "7664uiy"
    bridge = QuikBridge(sock)
    tester = QuikConnectorTest(bridge, acc)

    sock.setblocking(0)
    while not tester.weEnded:
        rrRes = tester.qbridge.phandler.readyRead()
        if not rrRes:
            tester.nextStep()
    
    print("finished")