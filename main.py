import socket
from qpy.event_manager import EVENT_BAR, EVENT_CALLBACK_INSTALLED, EVENT_CLOSE, EVENT_ORDERBOOK_SNAPSHOT, EVENT_DATASOURCE_SET, EVENT_MARKET, EVENT_QUOTESTABLE_PARAM_UPDATE, Event

from qpy.quik_bridge import QuikBridge
from qpy.subscription_manager import SubscriptionManager, SUBSCRIPTION_ORDERBOOK, SUBSCRIPTION_QUOTESTABLE

class QuikConnectorTest(object):
    def __init__(self, bridge: QuikBridge, account: str):
        self.qbridge = bridge
        self.account = account
        self.subscription_manager = SubscriptionManager(self.qbridge)
        self.msgId = 0
        self.sayHelloMsgId = None
        self.msgWasSent = False
        self.is_cls_list_request_sent = False
        self.is_params_request_sent = False
        self.is_orderbook_request_sent = False
        self.clsList = None
        self.is_ds_request_sent = False
        self.ds = None
        self.ds_sec_code = None
        self.setUpdCBReqId = None
        self.updCBInstalled = False
        self.updCnt = 0
        self.closeDsMsgId = None
        self.weEnded = False
        self.is_close_request_sent = False
        self.register_handlers()

    def on_orderbook_update(self, event: Event):
        print(f'OrderBookArrived: {event.data["sec_code"]}')
        if self.updCnt > 5 and self.canceled_order_id and not self.is_close_request_sent:
            self.closeDs()

    def on_quotes_table_update(self, event: Event):
        sec_code = event.data["sec_code"]
        event_string = event.to_json()
        print(f"{sec_code}: {event_string}")

    def on_classes_list(self, event: Event):
        self.clsList = event.data['classes'].split(",")
        self.clsList = list(filter(None, self.clsList))
        print("Received", len(self.clsList), "classes")

    def on_ds_created(self, event: Event):
        self.ds = event.data['ds']
        self.ds_sec_code = event.data["sec_code"]

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
        self.qbridge.register(EVENT_ORDERBOOK_SNAPSHOT, self.on_orderbook_update)
        self.qbridge.register(EVENT_MARKET, self.on_classes_list)
        self.qbridge.register(EVENT_BAR, self.on_bar_arrived)
        self.qbridge.register(EVENT_DATASOURCE_SET, self.on_ds_created)
        self.qbridge.register(EVENT_CALLBACK_INSTALLED, self.on_ds_update_handler_installed)
        self.qbridge.register(EVENT_CLOSE, self.on_ds_close)
        self.qbridge.register(EVENT_QUOTESTABLE_PARAM_UPDATE, self.on_quotes_table_update)
        
    def nextStep(self):
        if not self.msgWasSent:
            self.test_say_hello()
            self.msgWasSent = True
            self.test_global_callbacks()
        else:
            if self.clsList is None and not self.is_cls_list_request_sent:
                self.test_get_class_list()
            elif self.ds is None and not self.is_ds_request_sent:
                self.test_create_ds()
            elif not self.updCBInstalled:
                self.test_set_callback()
            elif not self.is_params_request_sent:
                self.subscribe(SUBSCRIPTION_QUOTESTABLE, "SPBFUT", "SiU3")
                self.is_params_request_sent = True
            elif not self.is_orderbook_request_sent:
                self.subscribe(SUBSCRIPTION_ORDERBOOK, "SPBFUT", "SiU3")
                self.is_orderbook_request_sent = True
            elif self.updCnt >= 3:
                if not self.is_close_request_sent:
                    self.closeDs()


    def test_say_hello(self):
        msg_id = self.qbridge.sayHello()
        self.sayHelloMsgId = msg_id

    def test_global_callbacks(self):
        self.qbridge.setGlobalCallback("OnOrder")
        self.qbridge.setGlobalCallback("OnTrade")

    def test_get_class_list(self):
        msg_id = self.qbridge.getClassesList()
        self.is_cls_list_request_sent = msg_id > 0

    def test_create_ds(self):
        msg_id = self.qbridge.createDs("SPBFUT", "SiU3", 5)
        self.is_ds_request_sent = msg_id > 0

    def test_set_callback(self):
        msg_id = self.qbridge.setDsUpdateCallback(self.ds, self.dsUpdated)
        self.updCBInstalled = msg_id > 0

    def closeDs(self):
        if self.ds is None:
            return
        msg_id = self.qbridge.closeDs(self.ds)
        self.is_close_request_sent = msg_id > 0

    def dsUpdated(self, ds, sec_code, index):
        print("dsUpdated:", index)
        self.qbridge.getBar(ds, "C", index)
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

    acc = "7664uiy"
    bridge = QuikBridge(sock)
    tester = QuikConnectorTest(bridge, acc)

    sock.setblocking(0)
    while not tester.weEnded:
        rrRes = tester.qbridge.phandler.readyRead()
        if not rrRes:
            tester.nextStep()
    
    print("finished")