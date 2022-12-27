import aiohttp
import aiomoex
import pandas as pd

from src.structures.st_strategies import DataRequest


async def get_security_history_aiomoex(request: DataRequest) -> dict:
    """
    Получить историю цен для указанной ценной бумаги.

    .. code-block:: python

        >>> import asyncio
        >>> req = get_security_history_aiomoex(DataRequest(['SBER'], '2022-11-05'))
        >>> asyncio.run(req)['SBER']['data']['close'].iloc[0]
        132.0

        >>> asyncio.run(get_security_history_aiomoex(DataRequest(['SBER', 'APPL'], '2022-11-05', '2022-11-05')))
        {'SBER': {'ok': True, 'message': '', 'data': Empty DataFrame
        Columns: []
        Index: []}, 'APPL': {'ok': False, 'message': 'Тикера APPL нет на MOEX', 'data': Empty DataFrame
        Columns: []
        Index: []}}

    :param request: Структура запроса StrategyRequest;
    :return: словарь с каждым тикером и историей цен.
    """

    # Из документации aiomoex : Размер свечки - целое число 1 (1 минута), 10 (10 минут), 60 (1 час), 24 (1 день),
    # 7 (1 неделя), 31 (1 месяц) или 4 (1 квартал)

    translate = {'1min': 1, '10min': 10, '1h': 60, '1d': 24, '1w': 7, '1m': 31, '1q': 4}

    interval = translate[request.dt_frequency.lower()]

    # Проверим что указаны необходимые
    async with aiohttp.ClientSession() as session:
        data = {}

        for ticker in request.tickers:
            flg = await check_availability_ticker(ticker)

            if flg['ok']:
                data[ticker] = {
                    'ok': True,
                    'message': '',
                    'lotsize': flg['data']['LOTSIZE'],
                    'data': pd.DataFrame(
                        await aiomoex.get_board_candles(
                            session,
                            security=ticker,
                            start=request.dt_start,
                            end=request.dt_end,
                            interval=interval
                        )
                    )
                }
            else:
                data[ticker] = {
                    'ok': False,
                    'message': f'Тикера {ticker} нет на MOEX',
                    'lotsize': None,
                    'data': pd.DataFrame()
                }

    return data


async def check_availability_ticker(ticker: str) -> dict[str, [bool, pd.Series]]:
    """
    Проверить доступность тикера.

    .. code-block:: python

        >>> import asyncio
        >>> asyncio.run(check_availability_ticker('SBER'))
        {'ok': True, 'data': REGNUMBER    10301481B
        LOTSIZE             10
        SHORTNAME     Сбербанк
        Name: SBER, dtype: object}

        >>> asyncio.run(check_availability_ticker('VKTRBR'))
        {'ok': False, 'data': None}

    """

    request_url = "https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json"
    arguments = {"securities.columns": "SECID," "REGNUMBER," "LOTSIZE," "SHORTNAME"}

    async with aiohttp.ClientSession() as session:
        iss = aiomoex.ISSClient(session, request_url, arguments)
        data = await iss.get()
        df = pd.DataFrame(data["securities"])
        df.set_index("SECID", inplace=True)

    return {'ok': True, 'data': df.loc[ticker]} if ticker in df.index else {'ok': False, 'data': None}


if __name__ == '__main__':
    import doctest

    doctest.testmod()
