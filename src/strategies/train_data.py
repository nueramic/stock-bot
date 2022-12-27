import asyncio

import pandas as pd

from moex_list import MOEX_LIST
from src.parse_securities.async_moex import get_security_history_aiomoex
from src.structures.st_strategies import DataRequest

data = asyncio.run(get_security_history_aiomoex(
    DataRequest(
        tickers=MOEX_LIST,
        dt_start='2018-01-01',
        dt_end='2022-10-01',
        dt_frequency='1d'
    )
))
data = pd.DataFrame(data).T
x = pd.DataFrame(columns=['close', 'date', 'ticker'])
for _, row in data.iterrows():
    if row['data'].shape[0] == 0:
        continue
    row.data['ticker'] = row.name
    row.data['date'] = row.data.begin.str.slice(0, 10)
    x = pd.concat([x, row.data[['close', 'date', 'ticker']]])

x.to_pickle('x.pkl')
print(x)
