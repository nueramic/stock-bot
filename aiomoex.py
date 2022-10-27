#!/usr/bin/env python
# coding: utf-8

# # Подключение библиотек

# In[20]:


# !pip install aiomoex


# In[61]:


import asyncio 

import aiohttp

import aiomoex
import pandas as pd


# # Параметры, которые будем использовать в примерах

# In[122]:


ticker = 'SBER'
start ='2022-10-08'
end = '2022-10-30'
columns = ['BOARDID', 'TRADEDATE', 'OPEN', 'CLOSE', 'VOLUME', 'VALUE']
interval = 60 


# # 0. Функция для вывода всех возможных тикеров библиотеки
# ### get_board_securities()

# In[142]:


async def get_board_securities():
    async with aiohttp.ClientSession() as session:
        data = pd.DataFrame(await aiomoex.get_board_securities(session))
    return data


# In[143]:


await get_board_securities()


# # 1. Получить интервал дат торгов тикером
# ### get_board_dates()

# In[112]:


# get_board_dates() позволяет узнать период дат, доступных значений котировок 
async with aiohttp.ClientSession() as session:
    dates = pd.DataFrame(await aiomoex.get_board_dates(session, ticker))
    print(dates)


# ### напишем нашу функцию get_board_dates() 

# In[98]:


async def get_board_dates(ticker):
    async with aiohttp.ClientSession() as session:
        dates = pd.DataFrame(await aiomoex.get_board_dates(session, ticker))
        return dates


# In[99]:


# Вызов асинхронной функции через await
await get_board_dates(ticker)


# # 2. Получить дневные значения цен по одному тикеру 
# ### get_board_history() 

# In[97]:


# aiomoex.get_board_history(session: aiohttp.client.ClientSession, security: str, start: Optional[str] = None, end: Optional[str] = None, columns: Optional[Iterable[str]] = 'BOARDID', 'TRADEDATE', 'CLOSE', 'VOLUME', 'VALUE', board: str = 'TQBR', market: str = 'shares', engine: str = 'stock') → List[Dict[str, Union[str, int, float]]]

# Получить историю торгов для указанной бумаги в указанном режиме торгов за указанный интервал дат.
async with aiohttp.ClientSession() as session:
    data = pd.DataFrame(await aiomoex.get_board_history(session, ticker, start, end, columns))
    print(data)


# ### напишем нашу функцию get_board_history() 

# In[102]:


async def get_board_history(ticker, start, end, columns):
    async with aiohttp.ClientSession() as session:
        data = pd.DataFrame(await aiomoex.get_board_history(session, ticker, start, end, columns))
    return data


# In[110]:


await get_board_history(ticker, start, end, columns)


# In[107]:


# Если поставить вместо значений start, end, columns 0, то будет использовано значение по умолчанию
# диапазон станет либо с самого начала торгов, либо до самого конца интервала торгов
# либо будут выведены все возможные столбцы данных


# In[109]:


await get_board_history(ticker, 0, 0, 0)


# ### get_market_history() 
# #### важность методов, содержащих market - разные board (BOARDID)

# In[113]:


# get_market_history - Получить историю по одной бумаге на рынке для всех режимов торгов за интервал дат.
# важность методов, содержащих market - разыне board (BOARDID)
async with aiohttp.ClientSession() as session:
    data = pd.DataFrame(await aiomoex.get_market_history(session, ticker))
    print(data)


# ### напишем нашу функцию get_market_history() 

# In[118]:


# get_market_history - Получить историю по одной бумаге на рынке для всех режимов торгов за интервал дат.
async def get_market_history(ticker, start, end, columns):
    async with aiohttp.ClientSession() as session:
        dates = pd.DataFrame(await aiomoex.get_market_history(session, ticker, start, end, columns))
    return dates


# In[119]:


await get_market_history(ticker, start, end, columns)


# In[121]:


# Если поставить вместо значений start, end, columns 0, то будет использовано значение по умолчанию
# диапазон станет либо с самого начала торгов, либо до самого конца интервала торгов
# либо будут выведены все возможные столбцы данных


# In[120]:


await get_market_history(ticker, 0, 0, 0)


# # 3. Исторические данные по свечкам 
# ### - возможность получить данные с гибким интервалом - минуты, часы, кварталы и тд
# * 1 - 1 минута
# 
# * 10 - 10 минут
# 
# * 60 - 1 час
# 
# * 24 - 1 день
# 
# * 7 - 1 неделя
# 
# * 31 - 1 месяц
# 
# * 4 - 1 квартал

# In[54]:


# get_board_candles - Получить свечи в формате HLOCV указанного инструмента в указанном режиме торгов за интервал дат. 
async with aiohttp.ClientSession() as session:
    data = pd.DataFrame(await aiomoex.get_board_candles(session, ticker, interval,  start, end))
    print(data)


# In[144]:


async def get_board_candles(ticker, interval,  start, end):
    async with aiohttp.ClientSession() as session:
        data = pd.DataFrame(await aiomoex.get_board_candles(session, ticker, interval,  start, end))
    return data


# In[150]:


await get_board_candles(ticker, interval,  start, end)


# In[159]:


# Посмотрим, как выгружает с интервалом минута за сегодняшний день
# Вижу задержку в 15 минут


# In[161]:


await get_board_candles(ticker, 1, '2022-10-27', 0)


# In[162]:


# # Аналогично с прошлыми примерами - есть функция get_market_candles() 

# Получить свечи в формате HLOCV указанного инструмента на рынке для основного режима торгов.
# Если торговля идет в нескольких основных режимах, то на один интервал времени может быть выдано несколько свечек - 
# по свечке на каждый режим. 
# Предположительно такая ситуация может произойти для свечек длиннее 1 дня.


# # Пример из документации на будущее о нескольких тикерах:
# ##### Вообще, вывод тот же, что и у get_board_securities()
# ##### Возможно, это пример реализации произвольного запроса 

# In[12]:


# Пример из документации: видимо выгрузка определенной информации из определенного места по нескольким тикерам
import asyncio

import aiohttp

import aiomoex
import pandas as pd


async def main():
    request_url = "https://iss.moex.com/iss/engines/stock/" "markets/shares/boards/TQBR/securities.json"
    arguments = {"securities.columns": ("SECID," "REGNUMBER," "LOTSIZE," "SHORTNAME")}

    async with aiohttp.ClientSession() as session:
        iss = aiomoex.ISSClient(session, request_url, arguments)
        data = await iss.get()
        df = pd.DataFrame(data["securities"])
        df.set_index("SECID", inplace=True)
        print(df.head(), "\n")
        print(df.tail(), "\n")
        df.info()

await main() 

