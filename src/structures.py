from typing import NamedTuple

import pandas as pd

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
    columns=list[str]
)

RequestManySecurities = NamedTuple(
    'many_request_template',
    tickers=list[str],
    start=str,
    end=str,
    columns=list[str]
)
