import asyncio
from collections import defaultdict
from copy import copy
from typing import Union

import pandas as pd
from pandas import Timestamp

from src.structures import SecurityState, StockPurchase


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
                    timestamp: Timestamp,
                    current_structure: dict[str, SecurityState],
                    received_structure: dict[str, SecurityState],
                    new_structure: dict[str, SecurityState]
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
            'current_structure': dict(current_structure),
            'received_structure': dict(received_structure),
            'new_structure': dict(new_structure),
        }

    def __repr__(self) -> str:
        return str(self.__history)

    def get_history(self):
        return self.__history


class Portfolio:

    def __init__(self, init_balance: [int, float] = 100_000):
        """
        Инициализация портфеля

        :param init_balance: начальный баланс портфеля
        """
        if not isinstance(init_balance, Union[int, float]):
            raise ValueError('Баланс должен быть числом типа int или float')

        self.__free_balance = init_balance  # баланс рублей в портфеле
        self.__full_balance = init_balance  # баланс с учетом ценности всех бумаг
        self.__securities = defaultdict(SecurityState)  # инициализируем пустой дефолтный словарь - портфель бумаг
        self.__history = PortfolioHistory()

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
    def history(self) -> dict:
        return self.__history.get_history()

    def _update_full_balance(self):
        """
        Обновляет полный баланс портфеля;
        """
        self.__full_balance = 0
        for security in self.__securities.values():
            self.__full_balance += security.amount * security.price

        self.__full_balance += self.__free_balance

    def update_securities(self, *args: StockPurchase) -> None:
        """
        Обновляет бумаги в портфеле.

        :param args: Кортежи (тикер, SecurityState). Если позиция короткая, то количество отрицательное.
                     Если бумаги были проданы или куплены количество соответственно положительное или отрицательное.
                     После обновления цена будет перевзвешена в соответствии с количеством. Если мы стоим в короткой
                     позиции, то покупка просто сократит количество бумаг, а на баланс может поступить положительная
                     разница, при ее наличии. Если в короткой позиции мы продаем бумаги, то их цена перевзвешивается;
        :return: обновляет внутренний портфель
        """
        current_structure = self.securities
        new_structure = dict()

        for security in args:
            security: StockPurchase
            new_structure[security.name] = SecurityState(security.amount, security.price)

            self._update_value_securities(security.name,
                                          SecurityState(security.amount, security.price),
                                          security.exchange_fees)

        asyncio.run(self.hook(current_structure, new_structure, copy(self.securities)))

    async def hook(self,
                   current_structure: dict[str, SecurityState],
                   received_structure: dict[str, SecurityState],
                   new_structure: dict[str, SecurityState]):
        """
        После любого обновления изменяет внутреннее состояние.

        :param current_structure: текущее состояние портфеля
        :param received_structure: полученное состояние портфеля
        :param new_structure: обновленное состояние портфеля
        """

        self.__history.log_history(
            self.__full_balance,
            pd.Timestamp.now(),
            current_structure,
            received_structure,
            new_structure
        )

    def _update_value_securities(self,
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

        cur_state: SecurityState = copy(self.__securities[security])

        # Если мы докупаем бумаги, то их количество увеличивается, и цена взвешивается. Баланс просто уменьшается

        # Мы без бумаг или в длинной позиции
        if cur_state.amount >= 0:

            # Покупаем бумаги
            if update_security_state.amount >= 0:
                self._same_directional_update(security, update_security_state)

            # Продаем бумаги
            else:
                self._different_directional_update(security, update_security_state)

        # Короткая позиция уже открыта
        else:
            # Покупаем бумаги
            if update_security_state.amount >= 0:
                self._different_directional_update(security, update_security_state)

            # Продаем бумаги
            else:
                self._same_directional_update(security, update_security_state)

        self.__free_balance -= exchange_fees
        self._update_full_balance()

    def _same_directional_update(self,
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

        # обновляем количество
        new_amount = cur_state.amount + update_security_state.amount

        # обновляем цену бумаги в портфеле
        new_price = cur_state.security_value() + update_security_state.security_value()
        new_price /= cur_state.amount + update_security_state.amount

        # обновляем баланс и состояние по бумаге
        self.__free_balance -= update_security_state.security_value()
        self.__securities[security].update_state(new_amount, new_price)
        self._update_full_balance()

    def _different_directional_update(self,
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
        if abs(cur_state.amount) > abs(update_security_state.amount):
            new_amount = cur_state.amount + update_security_state.amount
            new_price = cur_state.price

        # все продали / купили и вышли в другую позицию
        else:
            new_amount = cur_state.amount + update_security_state.amount
            new_price = update_security_state.price

        # обновляем баланс
        self.__free_balance -= update_security_state.security_value()
        self.__securities[security].update_state(new_amount, new_price)
        self._update_full_balance()


if __name__ == '__main__':
    port = Portfolio()
    print(port.securities, port.free_balance)

    port.update_securities(StockPurchase('SBER', 100, 120))
    print(port.securities, port.free_balance)

    port.update_securities(StockPurchase('SBER', -20, 100), StockPurchase('appl', 200, 200))
    print(port.securities, port.free_balance)

    port.update_securities(StockPurchase('SBER', -300, 140), StockPurchase('appl', -200, 210))
    print(port.securities, port.free_balance)

    print(port.securities['SBER'].history_sales)
    print(sum(port.securities['SBER'].history_sales))
    for epoch in port.history.items():
        print(epoch)
