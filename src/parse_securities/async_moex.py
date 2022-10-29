import aiohttp
import aiomoex
import pandas as pd

from ..structures import RequestOneSecurity


async def get_security_history(request: RequestOneSecurity) -> pd.DataFrame:
    async with aiohttp.ClientSession() as session:
        data = pd.DataFrame(
            await aiomoex.get_board_history(
                session,
                security=request.ticker,
                start=request.start,
                end=request.end,
                columns=request.columns
            )
        )
    return data

# TODO: сделать параллельный запрос нескольких бумаг на основе вызова одной бумаги.
#       использовать структуру RequestManySecurities. Эту структуру можно переработать и сделать более общей
