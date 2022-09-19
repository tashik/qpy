from dataclasses import dataclass
from typing import Any, Callable
from qpy.event_manager import EventManager, Event, EVENT_REQ_ARRIVED, EVENT_RESP_ARRIVED
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


    def closeDs(self, datasource):
        return self.send_request({"method": "invoke", "object": datasource, "function": "Close", "arguments": []}, {"message_type": "close_datasource", "datasource": datasource})

    def send_request(self, data: dict, meta_data: dict):
        msg_id = self.indexer.get_index()
        self.register_message(msg_id, data["function"], meta_data)
        self.phandler.sendReq(msg_id, data)
        return msg_id

    def on_req(self, id, data):
        self.phandler.sendAns(id, {"method": "return", "result": True})

    def on_resp(self, id, data):
        quik_message = self.message_registry[str(id)]

        if quik_message:
            # тут будет self.event_manager.put в зависимости от пришедших данных
            pass
        pass


class QuikConnectorTest(JsonProtocolHandler):
    def __init__(self, sock):
        super().__init__(sock)
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