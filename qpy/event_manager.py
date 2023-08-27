import json
from collections import defaultdict
from queue import Empty, Queue
from threading import Thread
from time import sleep
from typing import Any, Callable

EVENT_TIMER = "eTimer"
EVENT_PING = "ePing"
EVENT_TICK = "eTick."
EVENT_BAR = "eBar."
EVENT_ORDER_UPDATE = "eOnOrderUpdate"
EVENT_NEW_TRADE = "eOnNewTrade"
EVENT_ORDER_CANCEL = "eOrderCancel."
EVENT_POSITION = "ePosition."
EVENT_ACCOUNT = "eAccount."
EVENT_CONTRACT = "eContract."
EVENT_QUOTESTABLE_PARAM_UPDATE = "eQuoteTableUpdate."

EVENT_REQ_ARRIVED = "eRequest"
EVENT_RESP_ARRIVED = "eResponse"
EVENT_DATASOURCE_SET = "eDataSource"
EVENT_MARKET = "eMarket"
EVENT_ORDERBOOK = "eOrderBook"
EVENT_ORDERBOOK_SUBSCRIBE = "eOrderBookSubscribe"
EVENT_ORDERBOOK_SNAPSHOT = "eOrderbookSnapshot"
EVENT_CLOSE = "eDatasourceClose"
EVENT_CALLBACK_INSTALLED = "eDatasourceUpdateCallbackInstalled"


class Event:
    """
    Экземпляр события - это тип события (строка, которую EventEngine использует для проброса события) и данные,
    которые будут основным рабочим аргументом события)
    """

    def __init__(self, event_type: str, data: Any = None):
        """"""
        self.type = event_type
        self.data = data

    def to_dict(self):
        """"""
        data = self.data
        if not isinstance(data, dict):
            data = self.data.to_dict() if self.data else ""
        as_dict = {
            "type": self.type,
            "data": data
        }
        return as_dict

    def to_json(self):
        """"""
        as_dict = self.to_dict()
        json_string = json.dumps(as_dict)
        return json_string

# Определение обработчика (это функция с аргументом типа Event, которая не возвращает ничего
HandlerType = Callable[[Event], None]

class EventAware(object):
    def __init__(self):
        self.handlers = defaultdict(list)

    def register(self, event_type: str, handler: HandlerType):
        """
        Регистрация обработчика, подписка на событие (по типу)

        Parameters
        ----------
        event_type : str
            Название типа события (типы событий выведены в константы EVENT_* в event.defines)
        handler : HandlerType
            Ссылка на функцию-обработчик
        """
        handler_list = self.handlers[event_type]
        if handler not in handler_list:
            handler_list.append(handler)

    def fire(self, event: Event):
        if event.type in self.handlers:
                [handler(event) for handler in self.handlers[event.type]]