import socket
from qpy.event_manager import EVENT_BAR, EVENT_CALLBACK_INSTALLED, EVENT_CLOSE, EVENT_ORDERBOOK, EVENT_DATASOURCE, EVENT_MARKET, EVENT_TIMER, EventManager, Event

from qpy.quik_bridge import QuikBridge, QuikConnectorTest

class QuikConnectorTest(object):
    def __init__(self, bridge: QuikBridge):
        self.qbridge = bridge
        self.event_manager = self.qbrige.event_manager
        self.subscriptions = {}
        self.msgId = 0
        self.sayHelloMsgId = None
        self.msgWasSent = False
        self.is_cls_list_request_sent = False
        self.clsList = None
        self.is_ds_request_sent = False
        self.ds = None
        self.setUpdCBReqId = None
        self.updCBInstalled = False
        self.updCnt = 0
        self.closeDsMsgId = None
        self.register_handlers()

    def register_handlers(self):
        self.event_manager.register(EVENT_TIMER, self.update_subscriptions)
        self.event_manager.register(EVENT_ORDERBOOK, self.on_orderbook_update)
        self.event_manager.register(EVENT_MARKET, self.on_classes_list)
        self.event_manager.register(EVENT_BAR, self.reqArrived)
        self.event_manager.register(EVENT_DATASOURCE, self.on_ds_created)
        self.event_manager.register(EVENT_CALLBACK_INSTALLED, self.on_ds_update_handler_installed)
        self.event_manager.register(EVENT_CLOSE, self.on_ds_close)
        
    def update_subsciptions(self):
        if len(self.subscriptions) == 0:
            return
        for sub_type, subscriptions in self.subscriptions.items():
            for row in subscriptions:
                if sub_type == "orderbook":
                    self.qbridge.getOrderBook(row["class_code"], row["sec_code"])

    def on_orderbook_update(self, event: Event):
        self.ds = event.data['ds']

    def on_classes_list(self, event: Event):
        self.clsList = event.data['classes'].split(",")
        self.clsList = list(filter(None, self.clsList))
        print("Received", len(self.clsList), "classes")

    def on_ds_created(self, event: Event):
        self.ds = event.data['ds']

    def on_ds_close(self, event: Event):
        self.ds = None
        self.end()

    def on_ping(self, event: Event):
        print("hello sent")

    def on_ds_update_handler_installed(self, event: Event):
        print("update handler installed")

    def nextStep(self):
        if not self.msgWasSent:
            self.test_say_hello()
            self.msgWasSent = True
        else:
            if self.clsList is None and not self.is_cls_list_request_sent:
                self.test_get_class_list()
            elif self.ds is None and not self.is_ds_request_sent:
                self.test_create_ds()
            elif not self.updCBInstalled:
                self.test_set_callback()
            elif len(self.subscriptions) == 0:
                self.subscribe("orderbook", "TQBR", "SBER")
            elif self.updCnt >= 10:
                if not self.is_close_request_sent:
                    self.test_close_ds()

    def on_bar_arrived(self, event: Event):
        pass


    def test_say_hello(self):
        msg_id = self.qbridge.sayHello()
        self.sayHelloMsgId = msg_id
        self.updCnt += 1

    def test_get_class_list(self):
        msg_id = self.qbridge.getClassesList()
        self.is_cls_list_request_sent = msg_id > 0
        self.updCnt += 1

    def test_create_ds(self):
        msg_id = self.qbridge.createDs("TQBR", "SBER", 5)
        self.is_ds_request_sent = msg_id > 0
        self.updCnt += 1

    def test_set_callback(self):
        msg_id = self.qbridge.setDsUpdateCallback(self.ds, self.sberUpdated)
        self.updCBInstalled = msg_id > 0
        self.updCnt += 1

    def closeDs(self):
        if self.ds is None:
            return
        msg_id = self.qbridge.closeDs(self.ds)
        self.is_close_request_sent = msg_id > 0

    def sberUpdated(self, index):
        print("sberUpdated:", index)
        self.qbridge.getBar(self.ds, index)
        req = {"method": "invoke", "object": self.ds, "function": "C", "arguments": [index]}
        self.msgId += 1
        self.sendReq(self.msgId, req)
        return True

    def subscribe(self, subscription_type, class_code, sec_code):
        if subscription_type not in self.subscriptions.keys():
            self.subscriptions[subscription_type] = ()
        if subscription_type == "orderbook":
            msg_id = self.qbridge.subscribeToOrderBook(class_code, sec_code)
            self.subscriptions[subscription_type].add(
                {"class_code": class_code, "sec_code": sec_code, "msg_id": msg_id}
            )

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
    sock.setblocking(0)

    event_man = EventManager()
    bridge = QuikBridge(sock, event_man)
    tester = QuikConnectorTest(bridge)

    sock.setblocking(0)
    while not tester.weEnded:
        rrRes = tester.readyRead()
        if not rrRes:
            tester.nextStep()

    print("finished")