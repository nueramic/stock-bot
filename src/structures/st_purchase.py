from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.parse_securities.async_moex import get_security_history_aiomoex
from src.structures.st_strategies import DataRequest, TypeAction


class DataMessage:
    """
    Класс, в котором определена структура сообщения с данными.
    """

    def __init__(self, message_code: int = 0, message_text: str = ''):
        """
        Конструктор класса

        :param message_code: флаг. 0 - все окей данные есть. 1 - данных нет, так как скорее всего торги не ведутся.
                    2 - тикер не найден;
        :param message_text: сообщение
        """
        self.message_code = message_code
        self.message_text = message_text

    def __repr__(self) -> str:
        return f"DataMessage(flg={self.message_code}, message='{self.message_text}')"


class StockPurchaseRequest:

    def __init__(self,
                 ticker: str,
                 type_action: TypeAction,
                 amt_assets: float,
                 price: float = None,
                 dtime_now: str = None):
        """

        :param ticker: тикер инструмента;
        :param type_action: тип операции. 0 - ничего, -1 - продажа, 1 - покупка;
        :param amt_assets: сумма, которая доступна к покупке. Должна быть указана в валюте покупки;
        :param price: цена, за которую нужно купить. Если None, то покупка по рыночной цене;
        :param dtime_now: дата и время, когда был совершен запрос на покупку. Если None, то текущее время.
                          Для симуляций необходимо указывать дату и время, когда был совершен запрос на покупку.
                          Дата-время должны быть в формате '%Y-%m-%d %H:%M:%S' или '%Y-%m-%d'
        """
        self.ticker = ticker.upper()
        self.type_action = type_action
        self.price = price
        self.amt_assets = amt_assets
        self.dtime_now = dtime_now if dtime_now is not None else pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')

    def get_state(self) -> dict:
        """

        .. code-block:: python

            >>> StockPurchaseRequest('sBer', TypeAction.BUY, amt_assets=100, dtime_now='2022-12-17').get_state()
            {'ticker': 'SBER', 'type_action': 1, 'price': None, 'amt_assets': 100, 'dtime_now': '2022-12-17'}

        :return: Возвращает словарь с информацией о покупке
        """
        return self.__dict__

    def __repr__(self) -> str:
        return str(self.get_state())


class StockPurchaseResponse:

    def __init__(self,
                 message: DataMessage,
                 ticker: str,
                 market_price: float,
                 quantity: int,
                 lot_quantity: int,
                 dt_purchase: str = None,
                 exchange_fee: float = 0):
        """
        :param message: код + сообщение о том, как прошла покупка;
        :param ticker: Тикер бумаги
        :param market_price: Актуальная цена бумаги на рынке
        :param quantity: Количество купленных / проданных бумаг
        :param lot_quantity: Количество лотов, которое было куплено / продано
        :param dt_purchase: Дата и время покупки
        :param exchange_fee: Комиссия брокера
        """
        self.message = message
        self.ticker = ticker
        self.market_price = market_price
        self.quantity = quantity
        self.lot_quantity = lot_quantity
        self.exchange_fee = exchange_fee
        self.dt_purchase = dt_purchase if dt_purchase else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.type_purchase = TypeAction.BUY if quantity > 0 else TypeAction.SELL if quantity < 0 else TypeAction.NOTHING

    def __repr__(self) -> str:
        """
        :return: Возвращает строку с информацией о покупке
        """
        return f"StockPurchaseResponse(\n" \
               f"\tmessage={self.message}\n" \
               f"\tticker='{self.ticker}'\n" \
               f"\tmarket_price={self.market_price}\n" \
               f"\tquantity={self.quantity}\n" \
               f"\tlot_quantity={self.lot_quantity}\n" \
               f"\texchange_fee={self.exchange_fee}\n" \
               f"\ttype_purchase='{self.type_purchase}'\n)"


class StockPurchaseProcessMoex:

    def __init__(self, purchase_requests: list[StockPurchaseRequest]):
        """
        :param purchase_requests: запросы от стратегии
        """
        self.purchase_requests = purchase_requests
        self.data: dict = {}

    async def __call__(self) -> list[StockPurchaseResponse]:
        """
        Проводит процесс покупки и возращает StockPurchaseResponse. Нужно передать запросы на покупку.

        """
        await self._data_update()
        responses = []

        for req in self.purchase_requests:
            data = self.data[req.ticker]
            quantity = 0
            num_lots = 0

            market_price = None

            if data['ok'] and not data['data'].empty:
                market_price = data['data']['close'].iloc[-1]

                calc_quantity = await self.calc_purchase_quantity(market_price, req.amt_assets)
                num_lots = int(calc_quantity / data['lotsize'])
                calc_quantity = num_lots * data['lotsize']  # приводим к лотности

                if req.type_action == TypeAction.BUY:
                    quantity = calc_quantity

                elif req.type_action == TypeAction.SELL:
                    quantity = -calc_quantity
                else:
                    quantity = 0

            responses.append(
                StockPurchaseResponse(
                    message=(await self.generate_message(data)),
                    ticker=req.ticker,
                    market_price=market_price,
                    quantity=quantity,
                    lot_quantity=num_lots,
                )
            )
        return responses

    @staticmethod
    async def generate_message(moex_dict: dict) -> DataMessage:
        """
        Генерирует сообщение о покупке

        :param moex_dict: словарь с информацией о покупке;
        :return: код + сообщение о том, как прошла покупка
        """
        if moex_dict['ok']:
            if moex_dict['data'].shape[0] == 0:
                message_code = 1
                message_text = 'данных нет, так как скорее всего торги не ведутся'

            else:
                message_code = 0
                message_text = ''
        else:
            message_code = 2
            message_text = moex_dict['message']

        return DataMessage(message_code=message_code, message_text=message_text)

    @staticmethod
    async def calc_purchase_quantity(market_price: float, amt_assets: float) -> int:
        """
        Рассчитывает количество акций, которое можно купить на указанную сумму

        .. code-block:: python

            >>> import asyncio
            >>> asyncio.run(StockPurchaseProcessMoex.calc_purchase_quantity(market_price=100, amt_assets=1000))
            10
            >>> asyncio.run(StockPurchaseProcessMoex.calc_purchase_quantity(market_price=100, amt_assets=90))
            0
            >>> asyncio.run(StockPurchaseProcessMoex.calc_purchase_quantity(market_price=100, amt_assets=-1000))
            10

        :param market_price: цена акции;
        :param amt_assets: сумма, которую можно потратить на покупку;
        :return: словарь с информацией о покупке
        """

        quantity = int(abs(amt_assets) / market_price)  # количество акций, которое можно купить / продать
        return quantity

    async def _data_update(self) -> None:
        """
        Обновляет данные о бумаге;

        """
        data_request = DataRequest(
            tickers=[strategy_request.ticker for strategy_request in self.purchase_requests],
            dt_start=self.purchase_requests[0].dtime_now,
            dt_end=(pd.Timestamp(self.purchase_requests[0].dtime_now) +
                    pd.Timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S'),
            dt_frequency='1min'
        )
        self.data = await get_security_history_aiomoex(data_request)


if __name__ == '__main__':
    # import doctest
    import asyncio

    # doctest.testmod()

    reqs = [
        StockPurchaseRequest('sBer', TypeAction.BUY, 10000, dtime_now='2022-12-06 11:00:00'),
        StockPurchaseRequest('vtbr', TypeAction.SELL, 1000, dtime_now='2022-12-06 11:00:00'),
        StockPurchaseRequest('appl', TypeAction.NOTHING, 100, dtime_now='2022-12-06 11:00:00')
    ]

    process = StockPurchaseProcessMoex(reqs)
    resps = asyncio.run(process())

    print(resps)
