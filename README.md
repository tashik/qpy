# Qpy: фреймворк для взаимодействия с мостом QuikQtBridge

Код фреймворка находится в папке qpy, реализация взаимодействия с фреймворком показана в файле main.py. Файл test.py - это пример реализации взаимодействия с мостом [QuikQtBridge](https://github.com/tashik/QuikQtBridge), предоставленный разработчиком моста.

Все взаимодействие с Quik является асинхронным. Это значит, что на запрос мы не получим ответ сразу. Поэтому для того, чтобы внешняя относительно фреймворка система могла получать и обрабатывать данные, ей нужно зарегистрировать в классе EventManager обработчики событий. Пример регистрации смотреть в классе-тесте в main.py Список событий и форматы ответов приведу ниже, вместе с описанием методов запроса

Во все обработчики событий будет приходить один параметр event типа Event (см event_manager.py), который содержит два поля event_type: string и data: dict. Ниже описанный формат данных ответа - это то, что придет в обработчик в свойстве объекта event  в поле data.

На данный момент реализованы следующие методы в основном классе QuikBridge (по мере появления новых документация будет дополняться):

### sayHello():
        просто пинг, проверка связи
        событие *EVENT_PING*
        формат данных ответа - пусто

### getClassesList():
        запрос списка классов
        событие *EVENT_MARKET*
        формат данных ответа
            в поле event.data["classes"] строка со списком классов через запятую
            ```
            "TQPI,FQBR,FQDE,TQFD,CETS,INDXC,CETS_MTL,CETS_SU,SPBXM,SPBBND,SPBHKEX,SPBRU,SPBRUBND,SPBRU_USD,RTSIDX,USDRUB,CROSSRATE,EQRP_INFO,SMAL,INDX,TQBR,TQOB,TQIF,TQTF,TQBD,TQTD,TQOD,TQTE,TQCB,TQOE,TQIR,TQIU,SPBFUT,SPBOPT,FUTSPREAD,TQOY,OPTSPOT,SPBDE,FUTCLT,
            ```

### createDs(class_code: string, sec_code: string, interval: int):
        запрос на создание источника данных о свечах
        событие *EVENT_DATASOURCE_SET*
        формат данных ответа
        ```
        {
            "sec_code": string,
            "class_code": string,
            "interval": int,
            "ds": int - идентификатор источника данных, полученный от Quik
        }
        ```

### setDsUpdateCallback(datasource: int, callback: Callable = None):
        запрос на регистрацию обработчика данных из созданного источника данных (подписка на свечи)
        событие *EVENT_CALLBACK_INSTALLED*
        формат данных ответа
        ```
        {
            "sec_code": string,
            "class_code": None,
            "interval": None,
            "ds": int - идентификатор источника данных, куда проставился обработчик
        }
        ```

### getBar(datasource: int, bar_func: string, bar_index: int):
        запрос на получение данных свечи: тип данных определяется параметром bar_func, куда можно передать название любого поля, которое есть у свечи (см [документацию QLUA](https://luaq.ru/OHLCVT.html)), например, чтобы получить закрытие свечи, bar_func = 'C'
        событие *EVENT_BAR*
        формат данных ответа
        ```
        {
            "sec_code": string,
            "class_code": string,
            "interval": int,
            "field": string, - то что было передано в bar_func
            "value": mixed - значение поля свечи
        }
        ```

### closeDs(datasource: int):
        запрос на закрытие источника данных о свечаз
        событие *EVENT_CLOSE*
        формат данных ответа
        ```
        {
            "sec_code": string,
            "class_code": None,
            "interval": None,
            "ds": int - идентификатор источника данных, который был закрыт
        }
        ```

Часть данных может быть получена во внешнюю относительно фреймворка систему через функционал подписки. К этим типам данных относятся подписка на данные таблицы текущих торгов (пока там косяк у моста) и подписка на стаканы, которая сейчас реализована при помощи долбёжки по таймеру, но это будет исправлено, когда в мосте исправится косяк.

Все подписки осуществляются с помощью класса SubscriptionManager с простым интерфейсом в виде двух методов subscribe и unsubscribe. 

### subscribe(subscription_type: string, class_code: string, sec_code: string)
    запрос подписки нужного нам типа на нужный нам инструмент

### unsubscribe(subscription_type: string, class_code: string, sec_code: string)
    запрос отказа от подписки ненужного нам типа на ненужный нам уже инструмент

## Подписка на параметры таблицы текущих торгов

Тип подписки subscription_type - 'quotestable'.
Событие *EVENT_QUOTESTABLE_PARAM_UPDATE*
Формат данных события:

```
{
   "class_code": string,
   "sec_code": string,
   <имя параметра> : <значение параметра: string>
}
```

## Подписка на стаканы

Тип подписки subscription_type - 'orderbook'.
Событие *EVENT_ORDERBOOK_SNAPSHOT*
Формат данных события:

```
{
   "class_code": string,
   "sec_code": string,
   "order_book": {
    "bid": [
        {
            "price": "71251",
            "quantity": "4"
        },
        {
            "price": "71252",
            "quantity": "10"
        },
    ],
    "bid_count": "2.000000",
    "offer": [
        {
            "price": "71257",
            "quantity": "5"
        },
        {
            "price": "71258",
            "quantity": "1"
        },
    ], 
    "offer_count": "2.000000"
  }
}
```

## Работа с ордерами

Тестирование функциональности выполняется в отдельном файле testOrders.py

Для работы с ордерами используется один метод для всех действий - sendTransaction. Метод принимает на вход экземпляр класса TransactionEntity, содержащий информацию о транзакции
Помимо метода отправки транзакций, для работы с ордерами необходимо использовать событие OnTransReply и OnOrder. Чтобы его использовать, нужно зарегистировать глобальные коллбэки (см метод тестера test_global_callbacks).
При срабатывании обратного вызова OnOrder / OnTransReply система будет генерировать внутренее событие  *EVENT_ORDER_UPDATE*, на которое нужно подписаться уже в своем коде

### Пример размещения лимитного ордера:

```

from qpy.entities import TransactionEntity


sock = ... # подключение к сокету
acc = "87654abc" # номер счета
qBridge = QBridge(sock, acc)


client_code = "P123" # комментарий к ордеру
order_type = "L" # тип заявки (L - лимитный, M - рыночный)
transaction_id = qBridge.indexer.get_index() # уникальный идентификатор заявки на нашей стороне
class_code = "SPBFUT" # код класса инструмента
seccode = "SiU9" # код инструмента
qty = "1" # количество лотов
direction = "B" # направление сделки (B - покупка, S - продажа)
price = "90000" # цена лимитного ордера, для рыночного ордера на фонде передаем "0", для рыночного ордера на срочке передаем цену соответствующей границы ценового коридора
action = "NEW_ORDER"

tran = TransactionEntity(acc, client_code,  order_type, transaction_id, class_code, seccode, action, direction, price, qty)
qBridge.sendTransaction(tran)

```

### Пример отмены ордера:

Отменять мы можем только тот ордер, по которому приходил обратный вызов, потому что при отмене требуется передать order_num, который приходит от QUIK.

```

canceled_order_num = ... # идентификатор отменяемого ордера на стороне QUIK, который мы получили в обработчике обратного вызова
new_transaction_id = qBridge.indexer.get_index()
action = "KILL_ORDER"
tran = TransactionEntity(acc, client_code,  order_type, new_transaction_id, class_code, seccode, action, direction, price, qty, cancel_order_num)
qBridge.sendTransaction(tran)

```

### Событие поступления обратного вызова EVENT_ORDER_UPDATE

В поле data в событии обратного вызова будет представлен словарь *order*, по структуре как qpy.entities.OrderEntity (но НЕ ЭКЗЕМПЛЯР класса OrderEntity!!!), часть полей может отсутствовать. При обрабоотке следует обязательно сохранить присвоенный QUIK order_num в соотнесении с нашим trans_id. Состояние заявки оперделяется по полю flags, которое будет числовым. Дата и время размещения / снятия заявки будет представлена в виде словаря, по структуре как qpy.entitites.DateTime (но НЕ ЭКЗЕМПЛЯР класса DateTime!!!)


## Событие поступления обратного вызова при состоявшейся сделке EVENT_NEW_TRADE

В поле data в событии обратного вызова будет представлен словарь *trade*, по структуре как qpy.entities.TradeEntity (но НЕ ЭКЗЕМПЛЯР класса TradeEntity!!!), часть полей может отсутствовать. Учитывать сделки поможет присвоенный QUIK trade_num. Дата и время сделки будет представлена в виде словаря, по структуре как qpy.entitites.DateTime (но НЕ ЭКЗЕМПЛЯР класса DateTime!!!)

