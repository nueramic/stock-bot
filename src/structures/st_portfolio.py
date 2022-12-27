from collections import defaultdict
from copy import deepcopy
from typing import Union

import numpy as np
from pandas import Timestamp

from src.strategies.strategy_macd import get_decision_macd_conservative_strategy
from src.structures.st_purchase import *
from src.structures.st_securities import *
from src.structures.st_strategies import *

MOEX_RUSSIA_INDEX_TICKERS = ['GAZP', 'GLTR', 'MAGN', 'MGTS', 'SBER', 'TATN', ]


class Securities(defaultdict):

    def __repr__(self):
        return f'{self.__class__.__name__}({self.get_json()})'

    def get_json(self):
        return {k: v for k, v in self.items()}


class PortfolioHistory:
    def __init__(self):
        """
        Конструктор класса, отвечающего за историю по портфелю
        """
        self.__history: dict[  # словарь с ключом - номером изменения и данными: дата и время, размер портфеля и состав
            int, dict[
                str,
                Timestamp,
                float,
                dict[str, SecurityState],
                dict[str, SecurityState],
                dict[str, SecurityState]
            ]
        ] = dict()
        self.__counter = 0

    def log_history(self,
                    balance: [float, int],
                    timestamp: str,
                    current_structure: Securities,
                    received_structure: Securities,
                    new_structure: Securities
                    ):
        """
        Логирование состояния портфеля

        :param balance: новый баланс портфеля
        :param timestamp: дата и    время изменения
        :param current_structure: текущее состояние портфеля
        :param received_structure: полученное состояние портфеля
        :param new_structure: обновленное состояние портфеля
        :return: только обновляет историю
        """
        self.__counter += 1
        self.__history[self.__counter] = {
            'dt': timestamp,
            'balance': balance,
            'current_structure': current_structure.__repr__(),
            'received_structure': received_structure.__repr__(),
            'new_structure': new_structure.__repr__(),
        }

    def __repr__(self) -> str:
        return json.dumps(self.__history)

    def get_history(self):
        return json.dumps(self.__history)


class Portfolio:

    def __init__(self,
                 init_balance: [int, float] = 100_000,
                 tickers: list[str] = None,
                 weights: list[float] = None,
                 strategy: callable = None,
                 type_process: str = 'sim'):
        """
        Инициализация портфеля

        :param init_balance: начальный баланс портфеля;
        :param tickers: список тикеров акций, которые будут входить в портфель. Если не указан, то портфель будет
                        состоять из всех акций moex russia index;
        :param weights: веса акций в портфеле. Если не указаны, то все акции будут иметь одинаковый вес;
        :param strategy: стратегия, которая будет использоваться для обновления портфеля.
        :param type_process: тип процесса, в котором работает портфель. Может быть 'sim' или 'real', соответственно
                             симуляция или реальный процесс
        """
        if not isinstance(init_balance, Union[int, float]):
            raise ValueError('Баланс должен быть числом типа int или float')

        self.__free_balance = init_balance  # баланс рублей в портфеле
        self.__max_leverage = 0.75  # максимальный уровень плеча
        self.__full_balance = init_balance  # баланс с учетом ценности всех бумаг
        self.__securities = Securities(SecurityState)  # инициализируем пустой дефолтный словарь - портфель бумаг
        self.__history = PortfolioHistory()
        self.strategy = strategy
        if tickers is None:
            self.tickers = MOEX_RUSSIA_INDEX_TICKERS
        else:
            self.tickers = tickers

        if weights is None:
            self.weights = self.calc_shares(self.tickers) * self.__free_balance

        else:
            self.weights = (np.array(weights) / np.sum(weights)) * self.__free_balance

        self.available_structure = dict(zip(self.tickers, self.weights))

        if type_process != 'sim':
            raise NotImplementedError('Реальный процесс еще не реализован')

        self.__type_process = type_process if type_process in ['sim', 'real'] else 'sim'
        self.rate_sim_exchange_fee = 0.00125
        self.st_time = pd.Timestamp('2022-09-15 11:00:00')

        self.flg_end_process = False

    @staticmethod
    def calc_shares(tickers: list[str]) -> np.ndarray:
        """
        Расчет весов акций по ковариации

        :param tickers: датафрейм с ценами закрытия акций;
        :return: вектор весов акций
        """
        request = DataRequest(
            tickers=tickers,
            dt_start=(pd.Timestamp.now() - pd.Timedelta(days=365 * 3)).strftime('%Y-%m-%d'),
            dt_end=pd.Timestamp.now().strftime('%Y-%m-%d'),
            dt_frequency='1d'
        )

        data = asyncio.run(get_security_history_aiomoex(request))
        df_data = []
        for ticker, data in data.items():
            df_data.append(data['data']['close'].rename(ticker))

        df_data = pd.concat(df_data, axis=1)
        shares = (1 / (df_data / df_data.mean(axis=0)).cov()).values.diagonal()
        shares = shares / shares.sum()

        return shares

    @property
    def type_process(self) -> str:
        return self.__type_process

    @property
    def free_balance(self) -> float:
        return float(self.__free_balance)

    @property
    def full_balance(self) -> float:
        return float(self.__full_balance)

    @property
    def securities(self) -> dict:
        return self.__securities

    @property
    def history(self) -> str:
        return self.__history.get_history()

    async def _update_full_balance(self):
        """
        Обновляет полный баланс портфеля;
        """
        self.__full_balance = 0

        for security in self.__securities.values():
            self.__full_balance += security.quantity * security.price

        self.__full_balance += self.__free_balance

    async def update_securities(self, *args: StrategyResponse) -> None:
        """
        Обновляет бумаги в портфеле.

        :param args: Если позиция короткая, то количество отрицательное.
                     Если бумаги были проданы или куплены количество соответственно положительное или отрицательное.
                     После обновления цена будет перевзвешена в соответствии с количеством. Если мы стоим в короткой
                     позиции, то покупка просто сократит количество бумаг, а на баланс может поступить положительная
                     разница, при ее наличии. Если в короткой позиции мы продаем бумаги, то их цена перевзвешивается;

        :return: обновляет внутренний портфель
        """

        current_structure: Securities  # логирование в истории состояний по бумагам
        received_structure: Securities  # логирование в истории состояний по бумагам
        new_structure: Securities  # логирование в истории состояний по бумагам

        current_structure = deepcopy(self.__securities)
        received_structure = Securities()

        if self.__type_process == 'sim':
            for strategy_response in args:
                purchase_process = StockPurchaseProcessMoex(
                    purchase_requests=[
                        StockPurchaseRequest(
                            ticker=strategy_response.ticker,
                            type_action=strategy_response.type_action,
                            amt_assets=await self.calc_amount(strategy_response),
                            price=strategy_response.price,
                            dtime_now=strategy_response.dtime_now,
                        )
                    ]
                )
                response = (await purchase_process())[0]  # обрабатываем покупки по одной штуке
                received_state = deepcopy(SecurityState(
                    quantity=response.quantity,
                    price=response.market_price,
                    stop_loss=strategy_response.stop_loss,
                    take_profit=strategy_response.take_profit
                ))

                received_structure[strategy_response.ticker] = received_state
                await self._update_value_securities(
                    security=response.ticker,
                    update_security_state=received_state,
                    exchange_fees=received_state.security_value() * self.rate_sim_exchange_fee
                )

        if len(args) > 0:
            dtime = args[0].dtime_now

        else:
            dtime = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')

        await self.log_history(dtime, current_structure, deepcopy(received_structure), deepcopy(self.__securities))

    async def log_history(self,
                          timestamp: str,
                          current_structure: Securities,
                          received_structure: Securities,
                          new_structure: Securities):
        """
        После покупки логирует историю.

        :param timestamp: время совершения сделки. Формат '%Y-%m-%d %H:%M:%S' или '%Y-%m-%d'
        :param current_structure: текущее состояние портфеля
        :param received_structure: полученное состояние портфеля
        :param new_structure: обновленное состояние портфеля
        """

        await self._update_full_balance()
        self.__history.log_history(
            self.__full_balance,
            timestamp,
            current_structure,
            received_structure,
            new_structure
        )

    async def _update_value_securities(self,
                                       security: str,
                                       update_security_state: SecurityState,
                                       exchange_fees: float = 0) -> None:

        """
        Обновляет количество бумаг в портфеле и считает финансовый эффект, потом обновляет баланс

        :param security: имя бумаги;
        :param update_security_state: купленное / проданное количество бумаг и их стоимость;
        :param exchange_fees: комиссия за сделку с этой бумагой;
        :return: обновляет состояние портфеля и ничего не возвращает
        """
        self.available_structure[security] -= update_security_state.security_value()

        cur_state: SecurityState = deepcopy(self.__securities[security])
        # Если мы докупаем бумаги, то их количество увеличивается, и цена взвешивается. Баланс просто уменьшается

        # Мы без бумаг или в длинной позиции
        if cur_state.quantity >= 0:
            # Покупаем бумаги
            if update_security_state.quantity >= 0:
                await self._same_directional_update(security, update_security_state)

            # Продаем бумаги
            else:
                await self._different_directional_update(security, update_security_state)

        # Короткая позиция уже открыта
        else:
            # Покупаем бумаги
            if update_security_state.quantity >= 0:
                await self._different_directional_update(security, update_security_state)

            # Продаем бумаги
            else:
                await self._same_directional_update(security, update_security_state)

        self.__free_balance -= exchange_fees
        await self._update_full_balance()

    async def calc_amount(self, strategy_response: StrategyResponse) -> float:
        """
        Вычисляет количество бумаг для покупки / продажи

        :param strategy_response: ответ стратегии;
        :return: количество бумаг для покупки
        """
        if strategy_response.type_action == TypeAction.BUY:
            return await self.calc_amount_buy(strategy_response)

        elif strategy_response.type_action == TypeAction.SELL:
            return await self.calc_amount_sell(strategy_response)

    async def calc_amount_buy(self, strategy_response: StrategyResponse) -> float:
        """
        Расчет количества свободных денег для покупки

        :param strategy_response: ответ от стратегии на покупку;
        :return: количество свободных денег
        """

        amt_money_1 = self.available_structure[strategy_response.ticker]
        amt_money_2 = np.inf

        if strategy_response.quantity is not None:
            if strategy_response.price is None:
                price = await get_security_history_aiomoex(
                    DataRequest(
                        tickers=[strategy_response.ticker],
                        dt_start=strategy_response.dtime_now,
                        dt_end=(pd.Timestamp(strategy_response.dtime_now) + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                        dt_frequency='1d'
                    )
                )
                if not price[strategy_response.ticker]['ok']:
                    return 0
                if price[strategy_response.ticker]['data'].empty:
                    return 0
                price = price[strategy_response.ticker]['data']['close'].iloc[0]
            else:
                price = strategy_response.price

            if self.flg_end_process:
                amt_money_2 = price * abs(strategy_response.quantity) + price * 0.99
            else:
                amt_money_2 = price * abs(strategy_response.quantity)

        return min(amt_money_1, amt_money_2)

    async def calc_amount_sell(self, strategy_response: StrategyResponse) -> float:
        """
        Расчет количества бумаг для продажи

        :param strategy_response: ответ от стратегии на продажу;
        :return: количество бумаг
        """
        avail_amt = 0

        if strategy_response.price is None:
            price = await get_security_history_aiomoex(
                DataRequest(
                    tickers=[strategy_response.ticker],
                    dt_start=strategy_response.dtime_now,
                    dt_end=(pd.Timestamp(strategy_response.dtime_now) + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                    dt_frequency='1d'
                )
            )
            price = price[strategy_response.ticker]['data']['close'].iloc[0]
        else:
            price = strategy_response.price

        if strategy_response.quantity is not None:
            quantity = abs(strategy_response.quantity)  # Количество бумаг для продажи
        else:
            quantity = int(self.available_structure[strategy_response.ticker] / price)

        if self.__securities[strategy_response.ticker].quantity >= 0:

            # разница между количеством бумаг и количеством бумаг, которое нужно продать
            delta = self.__securities[strategy_response.ticker].quantity - quantity

            # Если у нас есть бумаги, причем продаем не больше чем имеем
            if delta >= 0:
                avail_amt += quantity * price

            # Если у нас есть бумаги, но мы хотим продать больше чем есть, то мы можем продать все бумаги
            # и продать еще на сумму, ограниченную свободным балансом * плечом
            else:
                avail_amt += self.__securities[strategy_response.ticker].quantity * price
                avail_amt += min(
                    -delta * price,  # Сумма, на которую мы хотим продать.
                    # Крышка - максимальная сумма, на которую мы можем продать
                    self.available_structure[strategy_response.ticker] * self.__max_leverage
                )
        else:  # self.__securities[strategy_response.ticker].quantity < 0
            avail_amt += min(
                quantity * price,
                self.available_structure[strategy_response.ticker] * self.__max_leverage
            )

        if self.flg_end_process:
            avail_amt = abs(avail_amt) + price * 0.99

        return abs(avail_amt)

    async def _same_directional_update(self,
                                       security: str,
                                       update_security_state: SecurityState) -> None:
        """
        Покупка бумаг в длинной (или без бумаг) или продажа в короткой. То есть количество имеющихся бумаг сейчас
        того же знака, что текущая операция по бумагам.

        :param security: имя бумаги;
        :param update_security_state: купленное количество бумаг и их стоимость;
        :return: обновляет состояние портфеля и ничего не возвращает
        """
        cur_state: SecurityState = self.__securities[security]

        if cur_state.quantity is None:
            cur_state.quantity = 0
        # обновляем количество
        new_quantity = cur_state.quantity + update_security_state.quantity

        # обновляем цену бумаги в портфеле
        new_price = cur_state.security_value() + update_security_state.security_value()
        if cur_state.quantity + update_security_state.quantity != 0:
            new_price /= cur_state.quantity + update_security_state.quantity

        else:
            new_price = 0

        # обновляем баланс и состояние по бумаге
        self.__free_balance -= update_security_state.security_value()
        self.__securities[security].update_state(new_quantity, new_price,
                                                 update_security_state.stop_loss,
                                                 update_security_state.take_profit)
        await self._update_full_balance()

    async def _different_directional_update(self,
                                            security: str,
                                            update_security_state: SecurityState) -> None:
        """
        Продажа бумаг в длинной позиции или покупка в короткой.

        :param security: имя бумаги;
        :param update_security_state: проданное количество бумаг и их стоимость;
        :return: обновляет состояние портфеля и ничего не возвращает
        """
        cur_state: SecurityState = self.__securities[security]

        # обновляем количество, если продали или купили не больше текущей позиции
        if abs(cur_state.quantity) > abs(update_security_state.quantity):
            new_quantity = cur_state.quantity + update_security_state.quantity
            new_price = cur_state.price

        # все продали / купили и вышли в другую позицию
        else:
            new_quantity = cur_state.quantity + update_security_state.quantity
            new_price = update_security_state.price

        # обновляем баланс
        self.__free_balance -= update_security_state.security_value()
        self.__securities[security].update_state(new_quantity, new_price)
        await self._update_full_balance()

    async def sell_all(self, dtime_now: str) -> None:
        """
        Продать все имеющиеся бумаги

        :param dtime_now: текущее время;
        :return: None
        """
        self.flg_end_process = True
        sell = []
        for security in self.__securities:
            pseudo_strategy_response = StrategyResponse(
                ticker=security,
                type_action=TypeAction.SELL if self.__securities[security].quantity > 0 else TypeAction.BUY,
                quantity=abs(self.__securities[security].quantity),
                dtime_now=dtime_now
            )
            sell.append(pseudo_strategy_response)

        await self.update_securities(*sell)

    async def check_st_tp(self):
        """
        Проверяет стоп-лосс и тейк профит

        :return: продает или покупает бумаги
        """
        sell = []
        for security in self.__securities:
            try:
                if self.__securities[security].quantity > 0:
                    if self.__securities[security].price < self.__securities[security].stop_loss:
                        sell.append(StrategyResponse(
                            ticker=security,
                            type_action=TypeAction.SELL,
                            quantity=abs(self.__securities[security].quantity),
                            dtime_now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        ))
                    elif self.__securities[security].price > self.__securities[security].take_profit:
                        sell.append(StrategyResponse(
                            ticker=security,
                            type_action=TypeAction.SELL,
                            quantity=abs(self.__securities[security].quantity),
                            dtime_now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        ))
                elif self.__securities[security].quantity < 0:
                    if self.__securities[security].price > self.__securities[security].stop_loss:
                        sell.append(StrategyResponse(
                            ticker=security,
                            type_action=TypeAction.BUY,
                            quantity=abs(self.__securities[security].quantity),
                            dtime_now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        ))
                    elif self.__securities[security].price < self.__securities[security].take_profit:
                        sell.append(StrategyResponse(
                            ticker=security,
                            type_action=TypeAction.BUY,
                            quantity=abs(self.__securities[security].quantity),
                            dtime_now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        ))
            except TypeError:
                pass
        await self.update_securities(*sell)

    async def call_strategy(self) -> None:
        """
        Вызывает стратегию

        :param dtime_now: текущее время;
        :return: None
        """
        self.st_time = self.st_time + pd.Timedelta(days=1)

        for ticker in self.available_structure.keys():
            # проверим что не выходной
            price = await get_security_history_aiomoex(DataRequest(
                tickers=[ticker],
                dt_start=self.st_time.strftime('%Y-%m-%d'),
                dt_end=(self.st_time + pd.Timedelta('1d')).strftime('%Y-%m-%d'),
                dt_frequency='1d'
            ))
            if price[ticker]['ok']:
                if not price[ticker]['data'].empty:
                    prices = await get_security_history_aiomoex(DataRequest(
                        tickers=[ticker],
                        dt_end=(self.st_time + pd.Timedelta('1D')).strftime('%Y-%m-%d'),
                        dt_start=(self.st_time - pd.Timedelta('50D')).strftime('%Y-%m-%d'),
                        dt_frequency='1d'
                    ))
                    st_response = await self.strategy(prices[ticker]['data'].close, ticker=ticker)
                    st_response.ticker = ticker
                    print(self.st_time, st_response)
                    await self.update_securities(st_response)

        await self.check_st_tp()
        if self.st_time >= pd.Timestamp.now():
            self.flg_end_process = True


if __name__ == '__main__':
    import asyncio
    import json
    from time import sleep

    port = Portfolio(init_balance=100_000, strategy=get_decision_macd_conservative_strategy)
    for i in range(30):
        try:
            asyncio.run(port.call_strategy())
            print(port.full_balance, port.securities)
        except Exception as e:
            print(f'время подождем : {e}')
            sleep(5)

    # print(port.securities, port.free_balance, port.available_structure)
    # i = 0
    # for i in tqdm(range(2)):
    #     asyncio.run(port.update_securities(
    #         *[StrategyResponse(ticker=ticker, type_action=TypeAction.SELL, quantity=20,
    #                            dtime_now=(pd.Timestamp('2022-12-20 11:00:00') + pd.Timedelta(days=i)
    #                                       ).strftime('%Y-%m-%d %H:%M:%S'), stop_loss=100, take_profit=200)
    #           for ticker in MOEX_RUSSIA_INDEX_TICKERS]
    #     ))
    #     print(port.securities)
    #     asyncio.run(port.check_st_tp())
    #
    # asyncio.run(port.sell_all(dtime_now=(pd.Timestamp('2022-12-20 11:00:00') + pd.Timedelta(days=i + 1)
    #                                      ).strftime('%Y-%m-%d %H:%M:%S')))
    #
    # print(port.free_balance, port.full_balance, port.securities)
    # print(port.history)
    # print(port.available_structure)
    # print(port.securities)
