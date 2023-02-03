from qpy.quik_bridge import QuikBridge

from qpy.event_manager import Event, EVENT_TIMER, EVENT_ORDERBOOK, EVENT_ORDERBOOK_SNAPSHOT, EVENT_ORDERBOOK_SUBSCRIBE

class SubscriptionManager(object):
    def __init__(self, qbridge: QuikBridge):
        self.qbridge = qbridge
        self.event_manager = qbridge.event_manager

        self.active_subscritions = {}
        self.awaiting_data_subscriptions = {}
        self.pending_subscriptions = {}

        self.target_subscriptions = {}
        self.register_handlers()


    def register_handlers(self):
        self.event_manager.register(EVENT_TIMER, self.update_subsciptions)
        self.event_manager.register(EVENT_ORDERBOOK, self.on_orderbook_update)
        self.event_manager.register(EVENT_ORDERBOOK_SUBSCRIBE, self.on_orderbook_subscribe)

    def update_subsciptions(self, event: Event):
        if not self.target_subscriptions:
            return
        
        for sub_key, msg_id in self.target_subscriptions.items():
            if sub_key in self.pending_subscriptions.keys():
                continue

            sub_type, class_code, sec_code = sub_key.split("_")
            if sub_type == "orderbook":
                get_msg_id = self.qbridge.getOrderBook(class_code, sec_code)
                self.active_subscritions[sub_key] = get_msg_id
                
    def subscribe(self, subscription_type, class_code, sec_code):
        subscription_key = self.build_key (subscription_type, class_code, sec_code)
        if subscription_key in self.target_subscriptions.keys():
            return
        
        self.target_subscriptions[subscription_key] = 0

        if subscription_type == "orderbook":
            msg_id = self.qbridge.subscribeToOrderBook(class_code, sec_code)
            self.target_subscriptions[subscription_key] = msg_id
            self.pending_subscriptions[subscription_key] = msg_id

    def unsubscribe(self, subscription_type, class_code, sec_code):
        subscription_key = self.build_key (subscription_type, class_code, sec_code)
        if subscription_key not in self.target_subscriptions.keys():
            return

        if subscription_type == "orderbook":
            self.qbridge.unsubscribeToOrderBook(class_code, sec_code)

            del self.target_subscriptions[subscription_key]
            self.pending_subscriptions.pop(subscription_key, None)
            self.active_subscritions.pop(subscription_key, None)
            

    def build_key(self, tp, cc, sc):
        return "_".join((tp, cc, sc))

    def on_orderbook_update(self, event: Event):
        tp = 'orderbook'
        cc = event.data["class_code"]
        sc = event.data["sec_code"]
        sub_key = self.build_key(tp, cc, sc)
        if sub_key not in self.target_subscriptions.keys():
            if sub_key in self.active_subscritions.keys():
                self.unsubscribe(tp, cc, sc)
                del self.active_subscritions[sub_key]
            return

        snap_event = Event(EVENT_ORDERBOOK_SNAPSHOT, event.data)
        self.event_manager.put(snap_event)

    def on_orderbook_subscribe(self, event: Event):
        tp = 'orderbook'
        cc = event.data["class_code"]
        sc = event.data["sec_code"]
        sub_key = self.build_key(tp, cc, sc)
        if sub_key not in self.pending_subscriptions.keys():
            return
        del self.pending_subscriptions[sub_key]
