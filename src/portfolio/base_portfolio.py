from collections import defaultdict
from typing import Union, NamedTuple

SecurityState = NamedTuple('AmountPrice', amount=int, price=float)


# TODO: Дописать функционал портфеля ценных бумаг

class Portfolio:

    def __init__(self, balance: [int, float] = 100_000):
        """
        Инициализация портфеля

        :param balance: начальный баланс портфеля
        """
        if not isinstance(balance, Union[int, float]):
            raise ValueError('Баланс должен быть числом типа int или float')

        self.balance = balance
        self.securities = defaultdict(SecurityState)  # инициализируем пустой дефолтный словарь - портфель бумаг

    def update_securities(self, *args: tuple[str, int, float]) -> None:
        """
        Обновляет бумаги в портфеле.

        :param args: Кортежи (тикер, количество, цена). Если позиция короткая, то количество отрицательное.
                     Если бумаги были проданы или куплены количество соответственно положительное или отрицательное.
                     После обновления цена будет перевзвешена в соответствии с количеством. Если мы стоим в короткой
                     позиции, то покупка просто сократит количество бумаг, а на баланс может поступить положительная
                     разница, при ее наличии. Если в короткой позиции мы продаем бумаги, то их цена перевзвешивается;
        :return: обновляет внутренний портфель
        """
        for val in args:
            pass

    def hook(self):
        pass

    def _update_value_securities(self,
                                 cur_sec_state: SecurityState,
                                 bought_sec_state: SecurityState) -> SecurityState:
        """
        Обновляет количество бумаг в портфеле и считает финансовый эффект, потом обновляет баланс

        :param cur_amount: текущее количество бумаг и их стоимость;
        :param new_amount: купленное / проданное количество бумаг и их стоимость;
        :return: новое количество бумаг в портфеле, их стоимость
        """

        if cur_sec_state.amount >= 0 and bought_sec_state.amount >= 0:
            new_amount = cur_sec_state.amount + bought_sec_state.amount
            new_value = cur_sec_state.amount * cur_sec_state.price + bought_sec_state.amount * bought_sec_state.price
            new_price = new_value / new_amount

        elif cur_sec_state.amount >= 0 and bought_sec_state.amount < 0:
            pass
        return SecurityState(new_amount, new_price)
