from dataclasses import dataclass
import json


class TransactionEntity:
    """
    Экземпляр транзакции. 
    Поля
    ACCOUNT="YY0070001234",
    CLIENT_CODE="XXX",
    TYPE="M",
    TRANS_ID="7",
    CLASSCODE="TQBR",
    SECCODE="HYDR",
    ACTION="NEW_ORDER",
    OPERATION="B",
    PRICE="0",
    QUANTITY="15"
    """

    def __init__(self, account, client_code, type, trans_id, classcode, seccode, action, operation, price, quantity, order_key = None, move_mode = None):
        """"""
        self.ACCOUNT = account
        self.CLIENT_CODE = client_code
        self.TYPE = type
        self.TRANS_ID = trans_id
        self.CLASSCODE = classcode
        self.SECCODE = seccode
        self.ACTION = action
        self.OPERATION = operation
        self.PRICE = price
        self.QUATITY = quantity
        self.ORDER_KEY = order_key
        self.MODE = move_mode

    def to_dict(self):
        """"""
        as_dict = {
            "ACCOUNT": self.ACCOUNT,
            "CLIENT_CODE": self.CLIENT_CODE,
            "TYPE": self.TYPE,
            "TRANS_ID": str(self.TRANS_ID),
            "CLASSCODE": self.CLASSCODE,
            "SECCODE": self.SECCODE,
            "ACTION": self.ACTION,
            "OPERATION": self.OPERATION,
            "PRICE": self.PRICE,
            "QUANTITY": self.QUATITY
        }
        if self.ORDER_KEY is not None:
            as_dict["ORDER_KEY"] = self.ORDER_KEY

        if self.MODE is not None and self.ACTION == "MOVE_ORDER":
            as_dict["MODE"] = self.MODE
        return as_dict

    def to_json(self):
        """"""
        as_dict = self.to_dict()
        json_string = json.dumps(as_dict)
        return json_string


@dataclass
class DateTime:
    mcs: int # Микросекунды
    ms: int # Миллисекунды
    sec: int # Секунды
    min: int # Минуты
    hour: int # Часы
    day: int # День
    week_day: int # Номер дня недели
    month: int # Месяц
    year: int # Год


@dataclass
class OrderEntity:
    """
    Экземпляр заявки. 
    Поля
    https://luaq.ru/OnOrder.html#param_table_6
    """

    order_num: str	# Номер заявки в торговой системе
    flags: int	# Набор битовых флагов
    brokerref: str # Комментарий, обычно: <код клиента>/<номер поручения>
    userid: str # Идентификатор трейдера
    firmid: str # Идентификатор фирмы
    account: str # Торговый счет
    price: float # Цена
    qty: int # Количество в лотах
    balance: int # Остаток
    value: float # Объем в денежных средствах
    accruedint: float # 	Накопленный купонный доход
    trans_id: str # Идентификатор транзакции
    client_code: str # Код клиента
    price2: float # Цена выкупа
    settlecode: str # Код расчетов
    uid: int # Идентификатор пользователя
    canceled_uid: int # Идентификатор пользователя, снявшего заявку
    exchange_code: str # Код биржи в торговой системе
    activation_time: int # Время активации
    linkedorder: int # Номер заявки в торговой системе
    expiry: int # Дата окончания срока действия заявки
    sec_code: str # Код бумаги заявки
    class_code: str # Код класса заявки
    datetime:	DateTime	# Дата и время
    withdraw_datetime:	DateTime	# Дата и время снятия заявки
    bank_acc_id: str # Идентификатор расчетного счета/кода в клиринговой организации
    value_entry_type: int # Способ указания объема заявки. Возможные значения: «0» – по количеству, «1» – по объему
    repoterm: int # Срок РЕПО, в календарных днях
    repovalue: int # Сумма РЕПО на текущую дату. Отображается с точностью 2 знака
    repo2value: int # Объём сделки выкупа РЕПО. Отображается с точностью 2 знака
    repo_value_balance: int # Остаток суммы РЕПО за вычетом суммы привлеченных или предоставленных по сделке РЕПО денежных средств в неисполненной части заявки, по состоянию на текущую дату. Отображается с точностью 2 знака
    start_discount: int # Начальный дисконт, в %
    reject_reason: str # Причина отклонения заявки брокером
    ext_order_flags: int # Битовое поле для получения специфических параметров с западных площадок
    min_qty: int # Минимально допустимое количество, которое можно указать в заявке по данному инструменту. Если имеет значение 0, значит ограничение по количеству не задано
    exec_type: int # Тип исполнения заявки. Возможные значения: «0» – «Значение не указано»; «1» – «Немедленно или отклонить»; «2» – «Поставить в очередь»; «3» – «Снять остаток»; «4» – «До снятия»; «5» – «До даты»; «6» – «В течение сессии»; «7» – «Открытие»; «8» – «Закрытие»; «9» – «Кросс»; «11» – «До следующей сессии»; «13» – «До отключения»; «15» – «До времени»; «16» –«Следующий аукцион»
    side_qualifier: int # Поле для получения параметров по западным площадкам. Если имеет значение «0», значит значение не задано
    acnt_type: int # Поле для получения параметров по западным площадкам. Если имеет значение «0», значит значение не задано
    capacity: int # Поле для получения параметров по западным площадкам. Если имеет значение «0», значит значение не задано
    passive_only_order: int # Поле для получения параметров по западным площадкам. Если имеет значение «0», значит значение не задано
    visible: int # Видимое количество. Параметр айсберг-заявок, для обычных заявок выводится значение: «0».


@dataclass
class TradeEntity:
    trade_num: int # Номер сделки в торговой системе
    order_num: int # Номер заявки в торговой системе
    brokerref: int # Комментарий, обычно: <код клиента>/<номер поручения>
    userid: int # Идентификатор трейдера
    firmid: int # Идентификатор дилера
    canceled_uid: int # Идентификатор пользователя, отказавшегося от сделки
    account: int # Торговый счет
    price: int # Цена
    qty: int # Количество бумаг в последней сделке в лотах
    value: int # Объем в денежных средствах
    accruedint: int # Накопленный купонный доход
    settlecode: int # Код расчетов
    cpfirmid: int # Код фирмы партнера
    flags: int # Набор битовых флагов
    price2: int # Цена выкупа
    reporate: int # Ставка РЕПО (%)
    client_code: int # Код клиента
    accrued2: int # Доход (%) на дату выкупа
    repoterm: int # Срок РЕПО, в календарных днях
    repovalue: int # Сумма РЕПО
    repo2value: int # Объем выкупа РЕПО
    start_discount: int # Начальный дисконт (%)
    lower_discount: int # Нижний дисконт (%)
    upper_discount: int # Верхний дисконт (%)
    block_securities: int # Блокировка обеспечения («Да»/«Нет»)
    clearing_comission: int # Клиринговая комиссия биржи
    exchange_comission: int # Комиссия Фондовой биржи
    tech_center_comission: int # Комиссия Технического центра
    settle_date: int # Дата расчетов
    settle_currency: int # Валюта расчетов
    trade_currency: int # Валюта
    exchange_code: int # Код биржи в торговой системе
    station_id: int # Идентификатор рабочей станции
    sec_code: int # Код бумаги заявки
    class_code: int # Код класса
    datetime: DateTime	# Дата и время
    bank_acc_id: int # Идентификатор расчетного счета/кода в клиринговой организации
    broker_comission: int # Комиссия брокера. Отображается с точностью до 2 двух знаков. Поле зарезервировано для будущего использования
    linked_trade: int # Номер витринной сделки в Торговой Системе для сделок РЕПО с ЦК и SWAP
    period: int # Период торговой сессии. Возможные значения: «0» – Открытие; «1» – Нормальный; «2» – Закрытие
    trans_id: int # Идентификатор транзакции
    kind: int # Тип сделки. Возможные значения: «1» – Обычная; «2» – Адресная; «3» – Первичное размещение; «4» – Перевод денег/бумаг; «5» – Адресная сделка первой части РЕПО; «6» – Расчетная по операции своп; «7» – Расчетная по внебиржевой операции своп; «8» – Расчетная сделка бивалютной корзины; «9» – Расчетная внебиржевая сделка бивалютной корзины; «10» – Сделка по операции РЕПО с ЦК; «11» – Первая часть сделки по операции РЕПО с ЦК; «12» – Вторая часть сделки по операции РЕПО с ЦК; «13» – Адресная сделка по операции РЕПО с ЦК; «14» – Первая часть адресной сделки по операции РЕПО с ЦК; «15» – Вторая часть адресной сделки по операции РЕПО с ЦК; «16» – Техническая сделка по возврату активов РЕПО с ЦК; «17» – Сделка по спреду между фьючерсами разных сроков на один актив; «18» – Техническая сделка первой части от спреда между фьючерсами; «19» – Техническая сделка второй части от спреда между фьючерсами; «20» – Адресная сделка первой части РЕПО с корзиной; «21» – Адресная сделка второй части РЕПО с корзиной; «22» – Перенос позиций срочного рынка
    clearing_bank_accid: int # Идентификатор счета в НКЦ (расчетный код)
    canceled_datetime: DateTime	# Дата и время снятия сделки
    clearing_firmid: int # Идентификатор фирмы - участника клиринга
    system_ref: int # Дополнительная информация по сделке, передаваемая торговой системой
    uid: int # Идентификатор пользователя на сервере QUIK