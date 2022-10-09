import json
from dataclasses import dataclass
from typing import Any, Callable
from qpy.event_manager import EVENT_BAR, EVENT_CALLBACK_INSTALLED, EVENT_PING,EVENT_CLOSE, EVENT_DATASOURCE_SET, EVENT_MARKET, EVENT_ORDERBOOK, EventManager, Event, EVENT_REQ_ARRIVED, EVENT_RESP_ARRIVED
from qpy.message_indexer import MessageIndexer
from qpy.protocol_handler import JsonProtocolHandler

@dataclass
class QuikBridgeMessage(object):
    id: int
    message_type: str
    method_name: str
    sec_code: str = ""
    class_code: str = ""
    interval: str = ""
    datasource: Any = None
    callback: Callable = None


class QuikBridge(object):
    def __init__(self, sock, event_manager: EventManager):
        self.event_manager = event_manager
        self.register_handlers()

        self.phandler = JsonProtocolHandler(sock, event_manager)
        self.indexer = MessageIndexer()
        
        self.message_registry = {}

    def register_handlers(self):
        self.event_manager.register(EVENT_REQ_ARRIVED, self.on_req)
        self.event_manager.register(EVENT_RESP_ARRIVED, self.on_resp)

    def register_message(self, id, method_name, meta_data: dict):
        msg = QuikBridgeMessage(id, meta_data["message_type"], method_name)
        if "sec_code" in meta_data.keys():
            msg.sec_code = meta_data["sec_code"]
        if "class_code" in meta_data.keys():
            msg.class_code = meta_data["class_code"]

        if "interval" in meta_data.keys():
            msg.interval = meta_data["interval"]

        if "datasource" in meta_data.keys():
            msg.datasource = meta_data["datasource"]

        if "callback" in meta_data.keys():
            msg.callback = meta_data["callback"]

        self.message_registry[str(id)] = msg

    def sayHello(self):
        return self.send_request({"method": "invoke", "function": "PrintDbgStr", "arguments": ["Hello from python!"]}, {"message_type": "hello"})

    def getClassesList(self):
        return self.send_request({"method": "invoke", "function": "getClassesList", "arguments": []}, {"message_type": "classes_list"})

    def createDs(self, class_code, sec_code, interval):
        return self.send_request({"method": "invoke", "function": "CreateDataSource", "arguments": [class_code, sec_code, interval]},
        {"message_type": "create_datasource", "sec_code": sec_code, "class_code": class_code, "interval": interval})

    def setDsUpdateCallback(self, datasource, callback: Callable = None):
        return self.send_request({"method": "invoke", "object": datasource, "function": "SetUpdateCallback", "arguments": [{"type": "callable", "function": "on_update"}]},
        {"message_type": "datasource_callback", "datasource": datasource, "callback": callback})

    def getBar(self, datasource, bar_func, bar_index):
        return self.send_request({"method": "invoke", "object": datasource, "function": bar_func, "arguments": [bar_index]}, {"message_type": "bar_"+bar_func, "datasoruce": datasource})

    def closeDs(self, datasource):
        return self.send_request({"method": "invoke", "object": datasource, "function": "Close", "arguments": []}, {"message_type": "close_datasource", "datasource": datasource})

    def subscribeToOrderBook(self, class_code, sec_code):
        return self.send_request(
            {"method": "invoke", "function": "Subscribe_Level_II_Quotes", "arguments": [class_code, sec_code]}, 
            {"message_type": "subscribe_orderbook", "class_code": class_code, "sec_code": sec_code}
            )

    def unsubscribeToOrderBook(self, class_code, sec_code):
        return self.send_request(
            {"method": "invoke", "function": "Unsubscribe_Level_II_Quotes", "arguments": [class_code, sec_code]}, 
            {"message_type": "unsubscribe_orderbook", "class_code": class_code, "sec_code": sec_code}
            )

    def getOrderBook(self, class_code, sec_code):
        return self.send_request(
            {"method": "invoke", "function": "getQuotesLevel2", "arguments": [class_code, sec_code]}, 
            {"message_type": "get_orderbook", "class_code": class_code, "sec_code": sec_code}
            )

    def send_request(self, data: dict, meta_data: dict):
        msg_id = self.indexer.get_index()
        self.register_message(msg_id, data["function"], meta_data)
        self.phandler.sendReq(msg_id, data)
        return msg_id

    def on_req(self, id, data):
        if data["method"] == "invoke":
            quik_message = self.message_registry[str(id)] # type: QuikBridgeMessage
            if quik_message.callback is not None:
                quik_message.callback(data["arguments"][0])

        self.phandler.sendAns(id, {"method": "return", "result": True})

    def on_resp(self, id, data):
        quik_message = self.message_registry[str(id)] # type: QuikBridgeMessage
        event_data = {
            "sec_code": quik_message.sec_code,
            "class_code": quik_message.class_code,
            "interval": quik_message.interval
        }
        event_type = EVENT_RESP_ARRIVED
        if quik_message:
            if quik_message.message_type == "create_datasource":
                event_data["ds"] = data['result'][0]
                event_type = EVENT_DATASOURCE_SET
            elif quik_message.message_type == "classes_list":
                event_data["classes"] = data["result"][0]
                event_type = EVENT_MARKET
            elif quik_message.message_type == "order_book":
                for entry in data["result"].values():
                    snapshot = json.load(entry)
                    if "bid_count" in snapshot.keys() and "offer_count" in snapshot.keys():
                        event_type = EVENT_ORDERBOOK
                        event_data["order_book"] = snapshot
            elif quik_message.message_type == "close_datasource":
                event_type = EVENT_CLOSE
            elif quik_message.message_type == "datasource_callback":
                event_type = EVENT_CALLBACK_INSTALLED
            elif quik_message.message_type == "hello":
                event_type = EVENT_PING
            elif quik_message.message_type == "bar_C":
                event_type = EVENT_BAR
                event_data["close"] = data["result"][0]

            event = Event(event_type, event_data)
            self.event_manager.put(event)
        
