from collections import defaultdict
from copy import copy
from typing import Union, Self

import pandas as pd
from pandas import Timestamp

PRICE_PRECISION = 16


class SecurityState:

    def __init__(self, amount: int = 0, price: float = 0):
        """
        Конструктор класса, который будет хранить состояние конкретной бумаги.

        :param amount: количество актива;
        :param price: цена актива
        """
        self.amount: int = amount
        self.price: float = round(price, PRICE_PRECISION)
        self.history_sales: list[float] = [amount * self.price] if amount != 0 else []

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
                tuple[tuple[str, SecurityState]]
            ]
        ] = dict()
        self.__counter = 0

    def log_history(self,
                    balance: [float, int],
                    timestamp: Timestamp,
                    securities: tuple[str],
                    sec_states: tuple[SecurityState]):
        """
        Логирование состояния портфеля

        :param balance: новый баланс портфеля
        :param timestamp: дата и    время изменения
        :param securities: название бумаги
        :param sec_states: количество и цена бумаги в портфеле
        :return: только обновляет историю
        """

        self.__counter += 1

        sec_states: list[SecurityState] = list(map(lambda x: x.short_state(), sec_states))
        self.__history[self.__counter] = {
            'dt': timestamp,
            'balance': balance,
            'structure': tuple(zip(securities, sec_states))
        }

    def __repr__(self) -> str:
        return str(self.__history)

    def get_history(self):
        return self.__history


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
        for security in args:
            security: StockPurchase
            self._update_value_securities(security.name,
                                          SecurityState(security.amount, security.price),
                                          security.exchange_fees)

        self.hook()

    def hook(self):
        sec_names = ['RUB']
        sec_states = [SecurityState(self.__free_balance, 1)]
        for name, state in self.__securities.items():
            sec_names.append(name)
            sec_states.append(state)

        sec_names: list[str]
        self.__history.log_history(self.__full_balance, pd.Timestamp.now(), tuple(sec_names), tuple(sec_states))

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

        cur_state: SecurityState = self.__securities[security]

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
        if abs(cur_state.amount) >= abs(update_security_state.amount):
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

    port.update_securities(StockPurchase('SBER', 200, 110), StockPurchase('appl', 200, 200))
    print(port.securities, port.free_balance)

    port.update_securities(StockPurchase('SBER', -300, 140), StockPurchase('appl', -200, 190))
    print(port.securities, port.free_balance)

    print(port.securities['SBER'].history_sales)
    print(sum(port.securities['SBER'].history_sales))
    for epoch in port.history.items():
        print(epoch)
