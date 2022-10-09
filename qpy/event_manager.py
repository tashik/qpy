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
EVENT_TRADE = "eTrade."
EVENT_ORDER = "eOrder."
EVENT_ORDER_CANCEL = "eOrderCancel."
EVENT_POSITION = "ePosition."
EVENT_ACCOUNT = "eAccount."
EVENT_CONTRACT = "eContract."

EVENT_REQ_ARRIVED = "eRequest"
EVENT_RESP_ARRIVED = "eResponse"
EVENT_DATASOURCE_SET = "eDataSource"
EVENT_MARKET = "eMarket"
EVENT_ORDERBOOK = "eOrderBook"
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
        as_dict = {
            "type": self.type,
            "data": self.data.to_dict() if self.data else ""
        }
        return as_dict

    def to_json(self):
        """"""
        as_dict = self.to_dict()
        json_string = json.dumps(as_dict)
        return json_string


# Определение обработчика (это функция с аргументом типа Event, которая не возвращает ничего
HandlerType = Callable[[Event], None]


class EventManager:
    """
    EventEngine пробрасывает объект события в зависимости от типа события всем зарегистрированным подписчикам на событие

    Кроме того, он генерит секундный таймер, который можно использовать для организации регулярных вычислений
    """

    def __init__(self, interval: int = 1):
        """
        Возможно изменить интервал для таймера (по умолчанию это одна секунда)
        """
        self._interval = interval
        self._queue = Queue()
        self._active = False
        self._thread = Thread(target=self._run)
        self._thread.name = "EventLoop"
        self._timer = Thread(target=self._run_timer)
        self._timer.name = "Timer"
        self._handlers = defaultdict(list)
        self._general_handlers = []

    def _run(self):
        """
        Берет событие из очереди и обрабатывает его
        """
        while self._active:
            try:
                event = self._queue.get(block=True, timeout=1)
                self._process(event)
            except Empty:
                pass

    def _process(self, event: Event):
        """
        Сначала событие пробрасывается обработчикам, которые слушают именно его (по типу),
        потом событие пробрасывается обработчикам, которые слушают вообще все события
        """
        if event.type in self._handlers:
            [handler(event) for handler in self._handlers[event.type]]

        if self._general_handlers:
            [handler(event) for handler in self._general_handlers]

    def _run_timer(self):
        """
        Генерация события таймера
        """
        while self._active:
            sleep(self._interval)
            event = Event(EVENT_TIMER)
            self.put(event)

    def start(self):
        """
        Запуск EventEngine
        """
        self._active = True
        self._thread.start()
        self._timer.start()

    def stop(self):
        """
        Остановка EventEngine
        """
        self._active = False
        self._timer.join()
        self._thread.join()

    def put(self, event: Event):
        """
        Постановка события в очередь
        Parameters
        ----------
        event : Event
        """
        self._queue.put(event)

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
        handler_list = self._handlers[event_type]
        if handler not in handler_list:
            handler_list.append(handler)

    def unregister(self, event_type: str, handler: HandlerType):
        """
        Отмена подписки обработчика на событие

        Parameters
        ----------
        event_type : str
            Название типа события (типы событий выведены в константы EVENT_* в event.defines)
        handler : HandlerType
            Ссылка на функцию-обработчик
        """
        handler_list = self._handlers[event_type]

        if handler in handler_list:
            handler_list.remove(handler)

        if not handler_list:
            self._handlers.pop(event_type)

    def register_general(self, handler: HandlerType):
        """
        Регистрация обработчика всех системных событий
        """
        if handler not in self._general_handlers:
            self._general_handlers.append(handler)

    def unregister_general(self, handler: HandlerType):
        """
        Отмена регистрации обработчика всех системных событий
        """
        if handler in self._general_handlers:
            self._general_handlers.remove(handler)