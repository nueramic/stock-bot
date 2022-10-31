import asyncio

import pandas as pd
import plotly.express as px

from src.parse_securities.async_moex import get_pandas_series, RequestOneSecurity
from src.portfolio.base_portfolio import SecurityState
from src.strategies.strategy_macd import get_decision_macd_conservative_strategy

TIMEFRAME = ['2022-04-10', '2022-10-30']


async def simulate_trading(ticker: str, balance: float) -> [float, list[float]]:
    """
    Возвращает итоговый баланс после торговли и график изменения баланса

    :param ticker: тикер;
    :param balance: начальный баланс;
    :return: итоговый баланс, изменение баланса, массив цен закрытия;
    """

    request = RequestOneSecurity(ticker, TIMEFRAME[0], TIMEFRAME[1], '1d', ['TRADEDATE', 'CLOSE'])
    prices = await get_pandas_series(request)

    security_state_portfolio = SecurityState(0, 0)

    balance_dynamic = [balance]

    for i in range(60, len(prices) - 1):
        price = prices.iloc[i]
        # У нас в портфеле есть бумаги на продажу
        if security_state_portfolio.amount > 0:

            # мы можем продать их по текущей цене тейк профита
            if price >= security_state_portfolio.take_profit:
                balance += price * security_state_portfolio.amount
                security_state_portfolio = SecurityState(0, 0)

            # нам нужно продать их по текущей цене стоп лосса
            elif price <= security_state_portfolio.stop_loss:
                balance += price * security_state_portfolio.amount
                security_state_portfolio = SecurityState(0, 0)

        # У нас в портфеле бумаги с обязательством на покупку
        elif security_state_portfolio.amount < 0:

            # мы можем купить их по текущей цене тейк профита
            if price <= security_state_portfolio.take_profit:
                balance += price * security_state_portfolio.amount
                security_state_portfolio = SecurityState(0, 0)

            # нам нужно купить их по текущей цене стоп лосса
            elif price >= security_state_portfolio.stop_loss:
                balance += price * security_state_portfolio.amount
                security_state_portfolio = SecurityState(0, 0)

        # Если у нас нет бумаг в портфеле, то мы можем совершить новую сделку
        else:
            decision = await get_decision_macd_conservative_strategy(prices.iloc[:i])
            if decision.flg_action == 1:
                amount = int(balance // price)
                security_state_portfolio = SecurityState(amount, price, decision.stop_loss, decision.take_profit)
                balance -= price * amount

            elif decision.flg_action == -1:
                amount = int(balance // price)
                security_state_portfolio = SecurityState(-amount, price, decision.stop_loss, decision.take_profit)
                balance += price * amount

        balance_dynamic.append(balance + security_state_portfolio.amount * price)
    else:
        if security_state_portfolio.amount != 0:
            balance += prices.iloc[-1] * security_state_portfolio.amount

    balance_dynamic.append(balance)

    return balance, pd.Series(balance_dynamic, index=prices.iloc[59:].index, name=f'{ticker} balance')


async def sim(balance: float = 100_000):
    """
    Запускает симуляцию торговли на всех тикерах. Выводит итоговый баланс и график изменения баланса.
    Сохраняет пандас датафрейм с торговлей по каждой бумаге в одну таблицу в excel.
    """

    tickers = ['SBER', 'GAZP', 'LKOH', 'ROSN', 'TATN', 'VTBR', 'YNDX', 'SNGS', 'MGNT', 'NVTK']

    balance_dynamics = []
    final_balances = []

    for ticker in tickers:
        final_balance, balance_dynamic = await simulate_trading(ticker, balance / len(tickers))
        balance_dynamics.append(balance_dynamic)
        final_balances.append(final_balance)

    final_balance = sum(final_balances)
    print(f'Итоговый баланс: {final_balance}')

    output_df = pd.concat(balance_dynamics, axis=1)
    output_df['Итоговый баланс'] = output_df.sum(axis=1)
    output_df.to_excel('output_macd_2022_11_01.xlsx')
    fig_by_tickers = px.line(output_df.iloc[:, :-1], title='<b>Динамика балансов по бумагам</b>')
    fig_by_tickers.to_html('balance_by_tickers_macd_2022_11_01.html')

    fig_full_balance = px.line(output_df.iloc[:, -1], title='<b>Динамика итогового баланса</b>')
    fig_full_balance.to_html('balance_full_macd_2022_11_01.html')


if __name__ == '__main__':
    asyncio.run(sim())
