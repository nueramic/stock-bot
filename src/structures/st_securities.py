from __future__ import annotations

from copy import copy

PRICE_PRECISION = 16


class StockSecurityPrice:

    def __init__(self, ticker: str, market_price: float):
        """
        Конструктор класс рыночной цены по бумаге

        :param ticker: тикер бумаги
        :param market_price: рыночная цена
        """
        self.ticker = ticker
        self.price = market_price


class SecurityState:

    def __init__(self,
                 quantity: int = 0,
                 price: float = 0,
                 stop_loss: float = None,
                 take_profit: float = None):
        """
        Конструктор класса, который будет хранить состояние конкретной бумаги.

        .. note:: Стоп лосс и тейк профит пока исполняют заявку по бумаге в полном объеме

        :param quantity: количество актива;
        :param stop_loss: Цена с целью ограничить свои убытки;
        :param take_profit: Цена, при которой мы получаем таргетированную выгоду;
        :param price: цена актива
        """
        self.quantity: int = quantity
        self.price: float = price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.history_security: list[dict] = [self._get_state()]

    def _get_state(self) -> dict:
        """

        .. code-block:: python

            >>> security_state = SecurityState(quantity=10, price=100)
            >>> security_state._get_state()
            {'quantity': 10, 'price': 100, 'sl': None, 'tp': None}

        """
        return {'quantity': self.quantity, 'price': self.price, 'sl': self.stop_loss, 'tp': self.take_profit}

    def __repr__(self) -> str:
        """

        .. code-block:: python

            >>> SecurityState(1, 2, 3, 4)
            {'quantity': 1, 'price': 2, 'sl': 3, 'tp': 4}

        :return: Возвращает строку с информацией о бумаге в портфеле
        """
        return str(self._get_state())

    def security_value(self) -> float:
        """
        Возвращает стоимость всех бумаг: quantity * price

        .. code-block:: python

            >>> SecurityState(quantity=2, price=12.5).security_value()
            25.0

        :return: стоимость всех бумаг
        """
        if self.price is not None and self.quantity is not None:
            return self.price * self.quantity
        else:
            return 0

    def update_state(self, new_quantity: int = 0, new_price: float = 0, sl: float = None, tp: float = None) -> None:
        """
        Обновляет состояние бумаги

        .. code-block:: python

            >>> security_state = SecurityState(1, 2, 3, 4)
            >>> security_state.update_state(5, 6)
            >>> security_state
            {'quantity': 5, 'price': 6, 'sl': 3, 'tp': 4}

            >>> security_state.history_security
            [{'quantity': 1, 'price': 2, 'sl': 3, 'tp': 4}, {'quantity': 5, 'price': 6, 'sl': 3, 'tp': 4}]

        :param new_quantity: количество актива;
        :param new_price: цена актива
        :param sl: Цена с целью ограничить свои убытки;
        :param tp: Цена, при которой мы получаем таргетированную выгоду;
        """

        self.quantity = new_quantity
        self.price = new_price
        self.stop_loss = sl
        self.take_profit = tp

        self.history_security.append(self._get_state())

    def short_state(self) -> SecurityState:
        """

        .. code-block:: python

            >>> security_state = SecurityState(1, 2, 3, 4)
            >>> security_state.short_state()
            {'quantity': 1, 'price': 2, 'sl': 3, 'tp': 4}

        :return: возвращает состояние бумаги без ее истории. Не изменяет объект
        """
        copy_self = copy(self)
        copy_self.history_security = []
        return copy_self


class InfoSecurityRequest:

    def __init__(self, ticker: str, start: str, end: str, time_step: str, columns: list[str]):
        """
        Конструктор класса для запроса данных с биржи.

        :param ticker: название бумаги;
        :param start: дата начала запроса;
        :param end: дата конца запроса;
        :param time_step: биржевой тик;
        :param columns: список столбцов
        """
        self.ticker: str = ticker
        self.start: str = start
        self.end: str = end
        self.time_step: str = time_step
        self.columns: list[str] = columns

    def __repr__(self) -> str:
        """

        .. code-block:: python

            >>> InfoSecurityRequest('SBER', '2021-01-01', '2021-01-02', '1min', ['close'])
            {'ticker': 'SBER', 'start': '2021-01-01', 'end': '2021-01-02', 'time_step': '1min', 'columns': ['close']}

        :return: Возвращает строку с информацией о запросе
        """
        return str({'ticker': self.ticker, 'start': self.start, 'end': self.end,
                    'time_step': self.time_step, 'columns': self.columns})


if __name__ == '__main__':
    import doctest

    doctest.testmod()
