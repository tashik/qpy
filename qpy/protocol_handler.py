from dataclasses import dataclass
import socket
import select
import json

from qpy.event_manager import EventAware, Event, EVENT_REQ_ARRIVED, EVENT_RESP_ARRIVED

@dataclass
class QMessage(object):
    id: int
    data: dict


class JsonProtocolHandler(EventAware):
    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        self.peerEnded = False
        self.weEnded = False
        self.incommingBuf = b''
        self.readable = None
        self.writable = None
        self.exceptional = None
        self.attempts = 0

    def sendReq(self, id, data, showInLog=True):
        if self.weEnded:
            return
        jobj = {"id": id, "type": "req", "data": data}
        stosend = json.dumps(jobj, separators=(',', ':'))
        if showInLog:
            print(f"SEND: {stosend}")
        self.sock.send(stosend.encode("utf-8"))

    def sendAns(self, id, data, showInLog=True):
        if self.weEnded:
            return
        jobj = {"id": id, "type": "ans", "data": data}
        stosend = json.dumps(jobj, separators=(',', ':'))
        if showInLog:
            print(f"REPLY: {stosend}")
        self.sock.send(stosend.encode("utf-8"))

    def sendVer(self, ver):
        if self.weEnded:
            return
        jobj = {"id": 0, "type": "ver", "version": ver}
        stosend = json.dumps(jobj, separators=(',', ':'))
        self.sock.send(stosend.encode("utf-8"))

    def end(self,  force=False):
        if self.weEnded and not force:
            return
        jobj = {"id": 0, "type": "end"}
        stosend = json.dumps(jobj, separators=(',', ':'))
        self.sock.send(stosend.encode("utf-8"))
        self.weEnded = True
        if self.peerEnded or force:
            self.sock.shutdown(2)
            self.sock.close()

    def reqArrived(self, id, data):
        print("REQ {:d}:".format(id))
        print("REQ CONTENT: " + json.dumps(data))
        event = Event(EVENT_REQ_ARRIVED, QMessage(id, data))
        self.fire(event)

    def ansArrived(self, id, data):
        if len(data) == 0: 
            print('empty resp')
            return
        event = Event(EVENT_RESP_ARRIVED, QMessage(id, data))
        
        print("ANS {:d}:".format(id))
        print("ANS CONTENT: " + json.dumps(data))

        self.fire(event)

    def processBuffer(self):
        try:
            strbuf = self.incommingBuf.decode("utf-8")
        except:
            return False
        if len(strbuf) == 0:
            return
        idx = 0
        for cc in strbuf:
            if cc == '{':
                if idx > 0:
                    strbuf = strbuf[idx:]
                    idx = 0
                break
            idx += 1
        if idx > 0:
            self.incommingBuf = strbuf.encode("utf-8")
            return False
        in_string = False
        in_esc = False
        brace_nesting_level = 0
        i = 0
        while i < len(strbuf):
            curr_ch = strbuf[i]
            if curr_ch == '"' and not in_esc:
                in_string = not in_string
                i += 1
                continue
            if not in_string:
                if curr_ch == '{':
                    brace_nesting_level += 1
                elif curr_ch == '}':
                    brace_nesting_level -= 1
                    if brace_nesting_level == 0:
                        sdoc = strbuf[:i+1]
                        if len(strbuf) == i + 1:
                            strbuf = ""
                        else:
                            strbuf = strbuf[i+1:]
                        self.incommingBuf = strbuf.encode("utf-8")
                        i = -1
                        in_string = False
                        in_esc = False
                        brace_nesting_level = 0
                        try:
                            jdoc = json.loads(sdoc)
                        except ValueError as err:
                            print("malformed json...")
                            jdoc = None
                        if jdoc is not None and len(jdoc) > 0:
                            if "id" in jdoc and "type" in jdoc:
                                if jdoc["type"] == "end":
                                    print("END received")
                                    self.peerEnded = True
                                    if self.weEnded:
                                        self.sock.shutdown(2)
                                        self.sock.close()
                                    return True
                                if jdoc["type"] == "ver":
                                    print("VER received")
                                    self.sendVer(1)
                                    return True
                                if jdoc["type"] == "ans" or jdoc["type"] == "req":
                                    data = jdoc["data"]
                                    if jdoc["type"] == "ans":
                                        self.ansArrived(jdoc["id"], data)
                                    else:
                                        self.reqArrived(jdoc["id"], data)
                                    return True
                        i += 1
                        continue
            else:
                if curr_ch == '\\' and not in_esc:
                    in_esc = True
                else:
                    in_esc = False
            i += 1
        return False

    def readyRead(self):
        if self.weEnded:
            return False
        inputs = [self.sock]
        outputs = []
        try:
            self.readable, self.writable, self.exceptional = select.select(inputs, outputs, inputs, 1)
        except select.error:
            self.sock.shutdown(2)
            self.sock.close()
            self.weEnded = True
            self.peerEnded = True
        if self.weEnded or self.peerEnded:
            return False
        if self.sock not in self.readable and self.sock not in self.exceptional:
            return False
        ndata = b''
        try:
            ndata = self.sock.recv(1024)
            # print(f"New data length {len(ndata)}")
        except socket.error:
            pass
        if ndata == b'' and self.attempts < 10:
            self.attempts += 1
            return False
        self.attempts = 0
        if not self.peerEnded:
            self.incommingBuf += ndata
            if self.processBuffer():
                self.attempts = 10
            return True
        return False