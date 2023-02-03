from qpy.quik_bridge import QuikBridge

from qpy.event_manager import Event, EVENT_ORDERBOOK, EVENT_ORDERBOOK_SNAPSHOT, EVENT_ORDERBOOK_SUBSCRIBE

SUBSCRIPTION_ORDERBOOK = "orderbook"
SUBSCRIPTION_QUOTESTABLE = "quotestable"

class SubscriptionManager(object):
    def __init__(self, qbridge: QuikBridge):
        self.qbridge = qbridge

        # self.param_list = [
        #     'CLASS_CODE',
        #     'CODE', 
        #     'MAT_DATE',
        #     'OPTIONBASE',
        #     'STRIKE',
        #     'VOLATILITY',
        #     'LAST',
        #     'BID',
        #     'BIDDEPTH',
        #     'OFFER',
        #     'OFFETDEPTH',
        #     'CLPRICE',
        #     'THEORPRICE',
        #     'OPTIONTYPE',
        #     'SEC_PRICE_STEP',
        #     'STEPPRICE',
        #     'SEC_SCALE',
        #     'CURRENTVALUE',
        #     'PRICEMIN',
        #     'PRICEMAX',
        #     'LOTSIZE'
        # ]

        self.param_list = [
            'BID',
            'OFFER',
            'BODDEPTH',
            'OFFERDEPTH',
            'LAST'
        ]

        self.active_subscritions = {}
        self.pending_subscriptions = {}

        self.target_subscriptions = {}
        self.register_handlers()


    def register_handlers(self):
        self.qbridge.register(EVENT_ORDERBOOK, self.on_orderbook_update)
        self.qbridge.register(EVENT_ORDERBOOK_SUBSCRIBE, self.on_orderbook_subscribe)
                
    def subscribe(self, subscription_type, class_code, sec_code):
        subscription_key = self.build_key (subscription_type, class_code, sec_code)
        if subscription_key in self.target_subscriptions.keys():
            return
        
        self.target_subscriptions[subscription_key] = 0

        if subscription_type == SUBSCRIPTION_ORDERBOOK:
            msg_id = self.qbridge.subscribeToOrderBook(class_code, sec_code)
            self.target_subscriptions[subscription_key] = msg_id
            self.pending_subscriptions[subscription_key] = msg_id
        elif subscription_type == SUBSCRIPTION_QUOTESTABLE:
            for param in self.param_list:
                msg_id = self.qbridge.subscribeToQuotesTableParams(class_code, sec_code, param)
            self.target_subscriptions[subscription_key] = msg_id
            self.active_subscritions[subscription_key] = msg_id


    def unsubscribe(self, subscription_type, class_code, sec_code):
        subscription_key = self.build_key (subscription_type, class_code, sec_code)
        if subscription_key not in self.target_subscriptions.keys():
            return

        if subscription_type == SUBSCRIPTION_ORDERBOOK:
            self.qbridge.unsubscribeToOrderBook(class_code, sec_code)

            del self.target_subscriptions[subscription_key]
            self.pending_subscriptions.pop(subscription_key, None)
            self.active_subscritions.pop(subscription_key, None)
            

    def build_key(self, tp, cc, sc):
        return "_".join((tp, cc, sc))

    def on_orderbook_update(self, event: Event):
        tp = SUBSCRIPTION_ORDERBOOK
        cc = event.data["class_code"]
        sc = event.data["sec_code"]
        sub_key = self.build_key(tp, cc, sc)
        if sub_key not in self.target_subscriptions.keys():
            if sub_key in self.active_subscritions.keys():
                self.unsubscribe(tp, cc, sc)
                del self.active_subscritions[sub_key]
            return

        snap_event = Event(EVENT_ORDERBOOK_SNAPSHOT, event.data)
        self.qbridge.fire(snap_event)

    def on_orderbook_subscribe(self, event: Event):
        tp = SUBSCRIPTION_ORDERBOOK
        cc = event.data["class_code"]
        sc = event.data["sec_code"]
        sub_key = self.build_key(tp, cc, sc)
        if sub_key in self.pending_subscriptions.keys():
            del self.pending_subscriptions[sub_key]

        get_msg_id = self.qbridge.getOrderBook(cc, sc)
        self.active_subscritions[sub_key] = get_msg_id

