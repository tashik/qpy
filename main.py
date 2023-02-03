import socket
from qpy.event_manager import EVENT_BAR, EVENT_CALLBACK_INSTALLED, EVENT_CLOSE, EVENT_ORDERBOOK_SNAPSHOT, EVENT_DATASOURCE_SET, EVENT_MARKET, EVENT_TIMER, EventManager, Event

from qpy.quik_bridge import QuikBridge
from qpy.subscription_manager import SubscriptionManager

class QuikConnectorTest(object):
    def __init__(self, bridge: QuikBridge):
        self.qbridge = bridge
        self.event_manager = self.qbridge.event_manager
        self.subscription_manager = SubscriptionManager(self.qbridge)
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
        self.weEnded = False
        self.register_handlers()

    def on_orderbook_update(self, event: Event):
        print(f'OrderBookArrived: {event.data["sec_code"]}')

    def on_classes_list(self, event: Event):
        self.clsList = event.data['classes'].split(",")
        self.clsList = list(filter(None, self.clsList))
        print("Received", len(self.clsList), "classes")

    def on_ds_created(self, event: Event):
        self.ds = event.data['ds']

    def on_ds_close(self, event: Event):
        self.ds = None
        self.qbridge.phandler.end()
        self.weEnded = True

    def on_ping(self, event: Event):
        print("hello sent")

    def on_ds_update_handler_installed(self, event: Event):
        print("update handler installed")

    def on_bar_arrived(self, event: Event):
        pass

    def register_handlers(self):
        self.event_manager.register(EVENT_ORDERBOOK_SNAPSHOT, self.on_orderbook_update)
        self.event_manager.register(EVENT_MARKET, self.on_classes_list)
        self.event_manager.register(EVENT_BAR, self.on_bar_arrived)
        self.event_manager.register(EVENT_DATASOURCE_SET, self.on_ds_created)
        self.event_manager.register(EVENT_CALLBACK_INSTALLED, self.on_ds_update_handler_installed)
        self.event_manager.register(EVENT_CLOSE, self.on_ds_close)
        
    def nextStep(self):
        if not self.msgWasSent:
            self.test_say_hello()
            self.msgWasSent = True
        else:
            if self.clsList is None and not self.is_cls_list_request_sent:
                self.test_get_class_list()
            elif self.ds is None and not self.is_ds_request_sent:
                self.test_create_ds()
            #elif not self.updCBInstalled:
                #self.test_set_callback()
            elif not self.subscription_manager.target_subscriptions:
                self.subscribe("orderbook", "SPBFUT", "SiH3")
            elif self.updCnt >= 10:
                if not self.is_close_request_sent:
                    self.test_close_ds()


    def test_say_hello(self):
        msg_id = self.qbridge.sayHello()
        self.sayHelloMsgId = msg_id
        self.updCnt += 1

    def test_get_class_list(self):
        msg_id = self.qbridge.getClassesList()
        self.is_cls_list_request_sent = msg_id > 0
        self.updCnt += 1

    def test_create_ds(self):
        msg_id = self.qbridge.createDs("SPBFUT", "SiH3", 5)
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
        self.subscription_manager.subscribe(subscription_type, class_code, sec_code)

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

    event_man = EventManager()
    event_man.start()
    bridge = QuikBridge(sock, event_man)
    tester = QuikConnectorTest(bridge)

    sock.setblocking(0)
    while not tester.weEnded:
        rrRes = tester.qbridge.phandler.readyRead()
        if not rrRes:
            tester.nextStep()

    print("finished")