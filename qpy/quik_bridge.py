from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable
from qpy.event_manager import EventAware, Event, EVENT_BAR, EVENT_CALLBACK_INSTALLED, EVENT_QUOTESTABLE_PARAM_UPDATE, EVENT_PING,EVENT_CLOSE, EVENT_DATASOURCE_SET, EVENT_MARKET, EVENT_ORDERBOOK, EVENT_ORDERBOOK_SUBSCRIBE, EVENT_REQ_ARRIVED, EVENT_RESP_ARRIVED
from qpy.message_indexer import MessageIndexer
from qpy.protocol_handler import JsonProtocolHandler, QMessage

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


class QuikBridge(EventAware):
    def __init__(self, sock):
        super().__init__()
        self.phandler = JsonProtocolHandler(sock)
        self.register_handlers()
        self.indexer = MessageIndexer()
        self.message_registry = {}
        self.data_sources = {}

    def register_handlers(self):
        self.phandler.register(EVENT_REQ_ARRIVED, self.on_req)
        self.phandler.register(EVENT_RESP_ARRIVED, self.on_resp)

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
            if meta_data["datasource"] not in self.data_sources:
                self.data_sources[meta_data["datasource"]] = { "sec_code": msg.sec_code}
            else:
                if msg.sec_code is None:
                    msg.sec_code = self.data_sources[meta_data["datasource"]]['sec_code']

        if "callback" in meta_data.keys():
            msg.callback = meta_data["callback"]
            if msg.datasource is not None and msg.datasource in self.data_sources.keys():
                self.data_sources[msg.datasource]['callback'] = meta_data['callback']

        if "param_name" in meta_data.keys():
            msg.param_name = meta_data["param_name"]

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

    def subscribeToQuotesTableParams(self, class_code, sec_code, param_name):
        return self.send_request(
            {"method": "subscribeParamChanges","class":class_code,"security":sec_code, "param": param_name},
            {"message_type": "subscribe_quotes_table", "class_code": class_code, "sec_code": sec_code}
        )

    def unsubscribeToQuotesTableParams(self, class_code, sec_code, param_name):
        return self.send_request(
            {"method": "unsubscribeParamChanges","class":class_code,"security":sec_code, "param": param_name},
            {"message_type": "subscribe_quotes_table", "class_code": class_code, "sec_code": sec_code}
        )

    def getOrderBook(self, class_code, sec_code):
        return self.send_request(
            {"method": "invoke", "function": "getQuoteLevel2", "arguments": [class_code, sec_code]}, 
            {"message_type": "get_orderbook", "class_code": class_code, "sec_code": sec_code}
            )

    def send_request(self, data: dict, meta_data: dict):
        msg_id = self.indexer.get_index()
        if "function" in data.keys():
            method = data["function"]
        else:
            method = data["method"]
        self.register_message(msg_id, method, meta_data)
        self.phandler.sendReq(msg_id, data)
        return msg_id

    def on_req(self, event: Event):
        id = event.data.id
        data = event.data.data
        if data["method"] == "invoke" and data['object'] in self.data_sources:
            quik_message = self.data_sources[data["object"]] # type: QuikBridgeMessage
            if 'callback' in quik_message.keys():
                quik_message['callback'](data['object'], quik_message['sec_code'], data["arguments"][0])

        if data["method"] == "paramChange":
            quik_message = None
            if id in self.message_registry:
                quik_message = self.message_registry[str(id)] # type: QuikBridgeMessage
            param_name = data["param"]
            param_value = data["value"]
            event_data = {
                "sec_code": data["security"],
                "class_code": data["class"],
                param_name: param_value
            }
            event = Event(EVENT_QUOTESTABLE_PARAM_UPDATE, event_data)
            self.fire(event)
            
        self.phandler.sendAns(id, {"method": "return", "result": True})

    def on_resp(self, event: Event):
        if not isinstance(event.data, QMessage):
            return
        data = event.data.data
        quik_message = None
        
        if event.data.id is not None:
            quik_message = self.message_registry[str(event.data.id)] # type: QuikBridgeMessage
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
            elif quik_message.message_type == "subscribe_orderbook":
                event_type = EVENT_ORDERBOOK_SUBSCRIBE
                event_data['subscription_type'] = 'orderbook'
            elif quik_message.message_type == "get_orderbook":
                for entry in data["result"]:
                    if "bid_count" in entry.keys() and "offer_count" in entry.keys():
                        event_type = EVENT_ORDERBOOK
                        event_data["order_book"] = entry
            elif quik_message.message_type == "close_datasource":
                event_type = EVENT_CLOSE
            elif quik_message.message_type == "datasource_callback":
                event_type = EVENT_CALLBACK_INSTALLED
            elif quik_message.message_type == "hello":
                event_type = EVENT_PING
            elif quik_message.message_type == "bar_C":
                event_type = EVENT_BAR
                event_data["close"] = data["result"][0]


            if event_type != EVENT_RESP_ARRIVED:
                system_event = Event(event_type, event_data)
                self.fire(system_event)
        else:
            event_string = event.to_json()
            print(f"UNKNOWN RESPOSE: {event_string}")
        
