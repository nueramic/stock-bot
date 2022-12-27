from __future__ import annotations

import pandas as pd


class TypeAction:
    """
    Класс, в котором определены флаги действий
    """

    NOTHING = 0
    BUY = 1
    SELL = -1


class StrategyResponse:
    """
    Класс, в котором определена общая структура ответа от стратегии
    """

    def __init__(self,
                 ticker: str = None,
                 type_action: TypeAction = TypeAction.NOTHING,
                 price: float = None,
                 quantity: int = None,
                 dtime_now: str = None,
                 stop_loss: float = None,
                 take_profit: float = None,
                 comment: str = None):
        """
        Конструктор класса

        :param ticker: название инструмента / стратегии
        :param type_action: флаг действия. 1 - покупка, -1 - продажа, 0 - ничего не делать
        :param price: цена
        :param quantity: количество акций
        :param dtime_now: дата и время
        :param stop_loss: стоп-лосс
        :param take_profit: тейк-профит
        :param comment: комментарий, описание действия, которое нужно совершить
        """

        self.ticker = ticker
        self.type_action = type_action
        self.price = price
        self.dtime_now = dtime_now
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.comment = comment
        self.quantity = quantity

    def __repr__(self):
        return f'StrategyResponse(' \
               f'\nticker : {self.ticker},' \
               f'\ntype_action : {self.type_action},' \
               f'\nprice : {self.price},' \
               f'\nquantity : {self.quantity},' \
               f'\ndtime_now : {self.dtime_now},' \
               f'\nstop_loss : {self.stop_loss},' \
               f'\ntake_profit : {self.take_profit},' \
               f'\ncomment : {self.comment})'


class DataRequest:

    def __init__(self,
                 tickers: list[str] = None,
                 dt_start: pd.Timestamp | str = None,
                 dt_end: pd.Timestamp | str = None,
                 dt_frequency: str = None,
                 columns: list[str] = ('TRADEDATE', 'CLOSE')):
        """
        Конструктор базового класса запроса стратегии.

        :param tickers: список тикеров, для которых нужно получить данные
        :param dt_start: дата и время начала периода
        :param dt_end: дата и время конца периода
        :param dt_frequency: частота данных
        :param columns: необходимые колонки, по умолчанию дата-время + цена закрытия
        """

        # TODO: добавить проверку типов

        if tickers is None:
            tickers = []

        if isinstance(tickers, str):
            tickers = [tickers]

        if dt_start is None:
            dt_start = pd.Timestamp.now() - pd.Timedelta(days=365)

        if dt_end is None:
            dt_end = pd.Timestamp.now()

        if dt_frequency is None:
            dt_frequency = '1D'

        if columns is None:
            columns = ('TRADEDATE', 'CLOSE')

        self.tickers = tickers
        self.dt_start = dt_start.strftime('%Y-%m-%d') if isinstance(dt_start, pd.Timestamp) else dt_start
        self.dt_end = dt_end.strftime('%Y-%m-%d') if isinstance(dt_end, pd.Timestamp) else dt_end
        self.dt_frequency = dt_frequency
        self.columns = columns

    def get_json(self):
        """
        Метод, который возвращает json-представление класса

        .. code-block:: python
            >>> DataRequest(['SBER'], pd.Timestamp('2021-01-01')).get_json()['tickers']
            ['SBER']

        :return: json-представление класса
        """

        return self.__dict__

    def __repr__(self):
        return f'{self.__class__.__name__}({self.get_json()})'


class BaseStrategy:
    """
    Базовый класс стратегии. При создании экземпляра класса, в качестве аргументов передаются:
    Необходимые параметры для работы конкретной стратегии.
    """

    def __init__(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        """

    def get_decision(self, *args, **kwargs) -> StrategyResponse:
        """
        Метод, который возвращает решение стратегии.

        :param args:
        :param kwargs:
        :return: StrategyResponse
        """
        raise NotImplementedError

    def get_request(self, *args, **kwargs) -> DataRequest:
        """
        Метод, который возвращает запрос стратегии.

        :param args:
        :param kwargs:
        :return: DataRequest
        """
        raise NotImplementedError


if __name__ == '__main__':
    import doctest

    doctest.testmod()
