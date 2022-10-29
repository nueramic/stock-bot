import asyncio

import aiohttp
import pandas as pd

from src.parse_securities.async_moex import get_security_history
from src.structures import StrategyResponseMACD, RequestOneSecurity


def calc_linear_macd(prices: pd.Series, short_period: int = 12, long_period: int = 26) -> pd.Series:
    """
    Возвращает pd.Series со значениями индикатора macd.
    MACD = EMA_s(prices) - EMA_l(prices).

    :param prices: массив цен (закрытия / открытия / и т.д.)
    :param short_period: размер окна для короткого экспоненциального скользящего среднего
    :param long_period: размер окна для длинного экспоненциального скользящего среднего
    :return: значения индикатора для каждого таймстемпа
    """
    ema_s = prices.ewm(span=short_period, min_periods=short_period).mean()
    ema_l = prices.ewm(span=long_period, min_periods=long_period).mean()
    return ema_s - ema_l


def calc_signal_linear_macd(prices: pd.Series,
                            short_period: int = 12,
                            long_period: int = 26,
                            signal_period: int = 4) -> pd.Series:
    """
    Возвращает значение EMA_t(MACD) - ema значений линейного MACD. При пересечении сигнальной линии снизу вверх
    такая ситуация является сигналом к покупке - цена идет вверх. При пересечении ema(macd) сверху вниз - нужно
    продавать актив.

    :param prices: массив цен (закрытия / открытия / и т.д.)
    :param short_period: размер окна для короткого экспоненциального скользящего среднего;
    :param long_period: размер окна для длинного экспоненциального скользящего среднего;
    :param signal_period: период для сглаживания индикатора macd;
    :return: series со значениями сигнала
    """
    return calc_linear_macd(prices, short_period, long_period).ewm(span=signal_period).mean()


async def get_decision_macd_conservative_strategy(prices: pd.Series, **kwargs) -> StrategyResponseMACD:
    """
    Возвращает ответ по консервативной стратегии macd на последний таймстемп.

    :param prices: массив цен (закрытия / открытия / и т.д.);
    :param kwargs: параметры для расчета сигнала:  short_period, long_period, signal_period;
    :return:
    """

    async with aiohttp.ClientSession():
        str_bull = await _get_decision_macd_cs_bullish(prices, **kwargs)
        str_bear = await _get_decision_macd_cs_bearish(prices, **kwargs)

    if str_bear.name is not None:
        return str_bear

    if str_bull.name is not None:
        return str_bull

    return str_bear


async def _get_decision_macd_cs_bearish(prices: pd.Series, ma_period: int = 60, **kwargs) -> StrategyResponseMACD:
    """
    Возвращает ответ по консервативной стратегии на понижение macd на последний таймстемп.

    :param prices: массив цен (закрытия / открытия / и т.д.);
    :param ma_period: период для скользящего среднего;
    :param kwargs: параметры для расчета сигнала:  short_period, long_period, signal_period;
    :return: dict с ответом от стратегии
    """
    signal = calc_signal_linear_macd(prices, **kwargs)
    if signal.iloc[-1] < 0 and (signal.iloc[-5:-2]).all():  # проверяем, что сигнал медвежий после бычьих
        ma_prices = prices.rolling(ma_period).mean()  # Находим скользящее среднее с большим окном
        delta = abs(ma_prices.iloc[-1] - prices.iloc[-1])
        st = prices.iloc[-1] + delta * 0.75
        tp = prices.iloc[-1] - delta * 0.75

        response = StrategyResponseMACD(
            'bearish-conservative',
            round(prices.iloc[-1], 2),
            prices.index[-1],
            round(st, 2),
            round(tp, 2)
        )
        return response

    return StrategyResponseMACD(None, None, None, None, None)


async def _get_decision_macd_cs_bullish(prices: pd.Series, ma_period: int = 60, **kwargs) -> StrategyResponseMACD:
    """
    Возвращает ответ по консервативной стратегии на повышение macd на последний таймстемп.

    :param prices: массив цен (закрытия / открытия / и т.д.);
    :param ma_period: период для скользящего среднего;
    :param kwargs: параметры для расчета сигнала:  short_period, long_period, signal_period;
    :return: dict с ответом от стратегии
    """
    signal = calc_signal_linear_macd(prices, **kwargs)
    if signal.iloc[-1] > 0 and (signal.iloc[-5:-2] < 0).all():  # проверяем, что сигнал бычий после медвежьих
        ma_prices = prices.rolling(ma_period).mean()  # Находим скользящее среднее с большим окном
        delta = abs(ma_prices.iloc[-1] - prices.iloc[-1])
        st = prices.iloc[-1] - delta * 0.75
        tp = prices.iloc[-1] + delta * 0.75

        response = StrategyResponseMACD(
            'bullish-conservative',
            round(prices.iloc[-1], 2),
            prices.index[-1],
            round(st, 2),
            round(tp, 2)
        )
        return response

    return StrategyResponseMACD(None, None, None, None, None)


async def test():
    """ Тест - скачиваем данные по сберу и запускаем нашу стратегию для каждой даты """
    req = RequestOneSecurity('SBER', '2022-04-01', '2022-09-01', ['TRADEDATE', 'CLOSE'])
    pr = await get_security_history(req)
    pr = pr.set_index('TRADEDATE')['CLOSE']

    async with asyncio.TaskGroup() as tg:
        responses = []
        for idx in range(80, len(pr)):
            response = tg.create_task(get_decision_macd_conservative_strategy(pr.iloc[0:idx + 1]))
            responses.append(response)

    for i in range(len(responses)):
        responses: list
        responses[i] = responses[i].result()

    print(responses)


if __name__ == '__main__':
    asyncio.run(test())
