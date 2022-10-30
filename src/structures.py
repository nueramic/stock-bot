from copy import copy
from typing import NamedTuple
from typing import Self

import pandas as pd

PRICE_PRECISION = 16

StrategyResponseMACD = NamedTuple(
    'strategy_macd',
    name=[str, None],
    price=[float, None],
    dt=[pd.Timestamp, None],
    stop_loss=[float, None],
    take_profit=[float, None]
)

RequestOneSecurity = NamedTuple(
    'request_template',
    ticker=str,
    start=str,
    end=str,
    time_step=str,
    columns=list[str]
)

RequestManySecurities = NamedTuple(
    'many_request_template',
    tickers=list[str],
    start=str,
    end=str,
    columns=list[str]
)

StockSecurityPrice = NamedTuple(
    'stock_price_of_security',
    ticker=str,
    market_price=float
)


class SecurityState:

    def __init__(self,
                 amount: int = 0,
                 price: float = 0,
                 stop_loss: float = None, take_profit: float = None):
        """
        Конструктор класса, который будет хранить состояние конкретной бумаги.

        .. note:: Стоп лосс и тейк профит пока исполняют заявку по бумаге в полном объеме

        :param amount: количество актива;
        :param stop_loss: Цена с целью ограничить свои убытки;
        :param take_profit: Цена, при которой мы получаем таргетированную выгоду;
        :param price: цена актива
        """
        self.amount: int = amount
        self.price: float = round(price, PRICE_PRECISION)
        self.history_sales: list[float] = [amount * self.price] if amount != 0 else []
        self.stop_loss = stop_loss
        self.take_profit = take_profit

    def __repr__(self) -> str:
        """
        :return: Возвращает строку с информацией о бумаге в портфеле
        """
        return str({'amount': self.amount, 'price': self.price})

    def security_value(self) -> float:
        """
        Возвращает стоимость всех бумаг: amount * price

        :return: стоимость всех бумаг
        """
        return self.price * self.amount

    def update_state(self, new_amount: int = 0, new_price: float = 0) -> None:
        """
        Обновляет состояние бумаги

        :param new_amount: количество актива;
        :param new_price: цена актива
        """

        self.history_sales.append(self.amount * self.price - new_amount * new_price)
        self.amount = new_amount
        self.price = round(new_price, PRICE_PRECISION)

    def short_state(self) -> Self:
        """
        :return: возвращает состояние бумаги без ее истории. Не изменяет объект
        """
        copy_self = copy(self)
        copy_self.history_sales = []
        return copy_self


class StockPurchase:

    def __init__(self, name: str, amount: int, price: float, exchange_fees: float = 0):
        """
        Конструктор класса покупки на бирже нового актива.
        :param name: название бумаги. Оно обязательно будет приведено к верхнему регистру;
        :param amount: количество купленных бумаг. Может быть отрицательным при продаже;
        :param price: цена продажи / покупки
        :param exchange_fees: комиссии по операции
        """
        self.name = name.upper()
        self.amount = int(amount)
        self.price = price
        self.exchange_fees = exchange_fees
