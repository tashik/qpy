# Qpy: фреймворк для взаимодействия с мостом QuikQtBridge

Код фреймворка находится в папке qpy, реализация взаимодействия с фреймворком показана в файле main.py. Файл test.py - это пример реализации взаимодействия с мостом [QuikQtBridge](https://github.com/tashik/QuikQtBridge), предоставленный разработчиком моста.

Все взаимодействие с Quik является асинхронным. Это значит, что на запрос мы не получим ответ сразу. Поэтому для того, чтобы внешняя относительно фреймворка система могла получать и обрабатывать данные, ей нужно зарегистрировать в классе EventManager обработчики событий. Пример регистрации смотреть в классе-тесте в main.py Список событий и форматы ответов приведу ниже, вместе с описанием методов запроса

Во все обработчики событий будет приходить один параметр event типа Event (см event_manager.py), который содержит два поля event_type: string и data: dict. Ниже описанный форма данных ответа - это то, что придет в обработчик в свойстве объекта event  в поле data.

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

## Подписка на стаканы

Тип подписки subscription_type - 'orderbook'.
Событие *EVENT_ORDERBOOK_SNAPSHOT*
Формат данных ответа:

```
{
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
```

