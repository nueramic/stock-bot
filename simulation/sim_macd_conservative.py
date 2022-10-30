import asyncio

import pandas as pd
import plotly.express as px

from src.parse_securities.async_moex import get_pandas_series, RequestOneSecurity
from src.portfolio.base_portfolio import Portfolio, StockPurchase
from src.strategies.strategy_macd import get_decision_macd_conservative_strategy


def sim(ticker: str = 'SBER'):
    timeframe = ['2020-01-01', '2022-10-30']
    request = RequestOneSecurity(ticker, timeframe[0], timeframe[1], '1d', ['TRADEDATE', 'CLOSE'])
    prices = asyncio.run(get_pandas_series(request))

    balance = 100_000
    port = Portfolio(balance)

    cur_tp = None
    cur_st = None
    cur_state = None
    flg_no_strat = True
    balance_dynamic = []

    for i in range(100, len(prices) - 1):
        print(prices.index[i], port.full_balance, prices.iloc[i]    )
        response = asyncio.run(get_decision_macd_conservative_strategy(prices.iloc[:i]))
        price = prices.iloc[i]
        if cur_state is None and response.name is not None and flg_no_strat:
            cur_state = response.name
            current_amount = balance // response.price
            if response.name == 'bearish-conservative':
                print(f'Продажа! {- current_amount}')
                purchase = StockPurchase(ticker, - current_amount, response.price)

            else:
                print(f'Покупка! {current_amount}')
                purchase = StockPurchase(ticker, current_amount, response.price)

            port.update_securities(purchase)
            cur_st = response.stop_loss
            cur_tp = response.take_profit

        elif cur_state == 'bearish-conservative':

            if price > cur_st or price < cur_tp:
                print(f'Покупка 1 ! {-port.securities[ticker].amount}')
                purchase = StockPurchase(ticker, -port.securities[ticker].amount, price)
                port.update_securities(purchase)
                cur_state = None
                flg_no_strat = True

        elif cur_state == 'bullish-conservative':
            if price < cur_st or price > cur_tp:
                print(f'Продажа 1 ! {port.securities[ticker].amount}')
                purchase = StockPurchase(ticker, port.securities[ticker].amount, price)
                port.update_securities(purchase)
                cur_state = None
                flg_no_strat = True

        balance_dynamic.append(port.full_balance)

    port.update_securities(StockPurchase(ticker, -port.securities[ticker].amount, prices.iloc[-1]))
    balance_dynamic.append(port.full_balance)

    fig = px.line(x=prices.index[100:], y=balance_dynamic, title=f'<b>{ticker} Стоимость портфеля</b>')

    fig.show()

    pd.DataFrame(port.history).T.to_csv('aaaa.csv')

sim()
sim('GAZP')
sim('TCSG')
