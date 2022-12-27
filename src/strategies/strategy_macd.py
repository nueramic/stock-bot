import asyncio

import aiohttp
import pandas as pd

from src.parse_securities.async_moex import get_security_history_aiomoex
from src.structures.st_strategies import StrategyResponse, DataRequest, TypeAction


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


async def get_decision_macd_conservative_strategy(prices: pd.Series, **kwargs) -> StrategyResponse:
    """
    Возвращает ответ по консервативной стратегии macd на последний таймстемп.

    :param prices: массив цен (закрытия / открытия / и т.д.);
    :param kwargs: параметры для расчета сигнала:  short_period, long_period, signal_period;
    :return:
    """

    async with aiohttp.ClientSession():
        str_bull = await _get_decision_macd_cs_bullish(prices, **kwargs)
        str_bear = await _get_decision_macd_cs_bearish(prices, **kwargs)

    if str_bear.type_action is not None:
        return str_bear

    if str_bull.type_action is not None:
        return str_bull

    return str_bear


# TODO: исправить на флаг продажи
async def _get_decision_macd_cs_bearish(prices: pd.Series, ma_period: int = 60, **kwargs) -> StrategyResponse:
    """
    Возвращает ответ по консервативной стратегии на понижение macd на последний таймстемп.

    :param prices: массив цен (закрытия / открытия / и т.д.);
    :param ma_period: период для скользящего среднего;
    :param kwargs: параметры для расчета сигнала:  short_period, long_period, signal_period;
    :return: dict с ответом от стратегии
    """
    signal = calc_signal_linear_macd(prices)
    if signal.iloc[-1] < 0 and (signal.iloc[-5:-2] > 0).all():  # проверяем, что сигнал медвежий после бычьих
        ma_prices = prices.rolling(ma_period).mean()  # Находим скользящее среднее с большим окном
        delta = abs(ma_prices.iloc[-1] - prices.iloc[-1])
        st = prices.iloc[-1] + delta * 0.75
        tp = prices.iloc[-1] - delta * 0.75

        response = StrategyResponse(
            ticker=kwargs['ticker'],
            type_action=TypeAction.SELL,
            price=prices.iloc[-1],
            stop_loss=st,
            take_profit=tp,
            comment=f'Сигнал медвежий: {signal.iloc[-1]}. Продаем по цене и ждем пока цена не достигнет {tp:.2f}.'
        )
        return response

    return StrategyResponse(comment='macd bearish conservative strategy is not triggered')


# TODO: исправить, чтобы цена округлялась по константе PRICE_ROUND
async def _get_decision_macd_cs_bullish(prices: pd.Series, ma_period: int = 60, **kwargs) -> StrategyResponse:
    """
    Возвращает ответ по консервативной стратегии на повышение macd на последний таймстемп.

    :param prices: массив цен (закрытия / открытия / и т.д.);
    :param ma_period: период для скользящего среднего;
    :param kwargs: параметры для расчета сигнала:  short_period, long_period, signal_period;
    :return: dict с ответом от стратегии
    """
    signal = calc_signal_linear_macd(prices)
    if signal.iloc[-1] > 0 and (signal.iloc[-5:-2] < 0).all():  # проверяем, что сигнал бычий после медвежьих
        ma_prices = prices.rolling(ma_period).mean()  # Находим скользящее среднее с большим окном
        delta = abs(ma_prices.iloc[-1] - prices.iloc[-1])
        st = prices.iloc[-1] - delta * 0.75
        tp = prices.iloc[-1] + delta * 0.75

        response = StrategyResponse(
            ticker=kwargs['ticker'],
            type_action=TypeAction.BUY,
            price=prices.iloc[-1],
            stop_loss=st,
            take_profit=tp,
            comment=f'Сигнал бычий: {signal.iloc[-1]}. Покупаем по цене и ждем пока цена не достигнет {tp:.2f}.'
        )
        return response

    return StrategyResponse()


async def test():
    """ Тест - скачиваем данные по сберу и запускаем нашу стратегию для каждой даты """
    req = DataRequest(['SBER'], '2022-04-01', '2022-09-01', '1d', ['TRADEDATE', 'CLOSE'])
    pr = await get_security_history_aiomoex(req)
    print(pr)
    pr = pr['SBER']['data'].set_index('begin')['close']

    responses = []
    for idx in range(80, len(pr)):
        response = await get_decision_macd_conservative_strategy(pr.iloc[0:idx + 1], ticker='sber')
        responses.append(response)

    for i in range(len(responses)):
        print(f'{i}: {responses[i].comment}')

    print(responses)


if __name__ == '__main__':
    asyncio.run(test())
