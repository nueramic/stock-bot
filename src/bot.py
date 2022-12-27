from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from aiogram.utils.helper import Helper, HelperMode, ListItem

from config import TOKEN
from src.strategies.strategy_macd import get_decision_macd_conservative_strategy
from src.structures.st_portfolio import Portfolio
import json

class TestStates(Helper):
    mode = HelperMode.snake_case

    TEST_STATE_0 = ListItem()
    TEST_STATE_1 = ListItem()
    TEST_STATE_2 = ListItem()
    TEST_STATE_3 = ListItem()
    TEST_STATE_4 = ListItem()
    TEST_STATE_5 = ListItem()


help_message = 'Для того, чтобы запустить симуляцию необходимо ввести значения тикеров, сумму и веса на каждый тикер. \n' \
               'Команда "/Добавить тикеры", включает режим добавления тикеров \n' \
               'Команда "/Добавить сумму", включает режим добавления суммы \n' \
               'Команда "/Добавить веса", включает режим добавления весов по тикерам \n\n' \
               'Чтобы сбросить текущее состояние, отправь "/Отмена".'

start_message = 'Привет, {name}! Это бот для проекта по ММТС! \n\n' + help_message
invalid_key_message = 'Ключ "{key}" не подходит.\n' + help_message
state_change_success_message = 'Текущее состояние успешно изменено'
state_reset_message = 'Процесс отменен \n\n' + help_message
current_state_message = 'Текущее состояние - "{current_state}"'
get_tickers_message = 'Пожалуйста, выберите из предложенного списка тикеры, которые добавите в свой портфель. \n\nКогда будете готовы перейти к следующему этапу - нажмите кнопку \n/set_sum'
get_sum_message = 'Теперь введите сумму'
get_weights_message = 'Теперь запишите значения весов на каждый тикер через запятую. \n\nВажные замечания: \nСумма весов должна быть равна 1. \nДесятичный разделитель - "."'

# ДОБАВИЛ Я
portfolio_exists = False
portfolio: Portfolio

MESSAGES = {
    'start': start_message,
    'help': help_message,
    'get_tickers': get_tickers_message,
    'get_sum': get_sum_message,
    'get_weights': get_weights_message,
    'invalid_key': invalid_key_message,
    'state_change': state_change_success_message,
    'state_reset': state_reset_message,
    'current_state': current_state_message,
}

btn0 = KeyboardButton('/Добавить_тикеры')
btn1 = KeyboardButton('/Добавить_сумму')
btn2 = KeyboardButton('/Добавить_веса')
btn3 = KeyboardButton('/Запустить_симуляцию')
btn_cancel = KeyboardButton('/Отмена')

ticker1 = KeyboardButton('GAZP')
ticker2 = KeyboardButton('GLTR')
ticker3 = KeyboardButton('MAGN')
ticker4 = KeyboardButton('MGTS')
ticker5 = KeyboardButton('SBER')
ticker6 = KeyboardButton('TATN')

tickers = []
summa = 0
weights = []

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    markup0 = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    await message.reply(MESSAGES['start'].format(name=message.from_user.first_name),
                        reply_markup=markup0.add(btn0).add(btn_cancel))


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply(MESSAGES['help'])


@dp.message_handler(state='*', commands=['set_tickers', 'Добавить_тикеры'])
async def set_tickers_command(message: types.Message):
    markup1 = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    #     markup1.row(ticker1, ticker2)
    #     markup1.row(ticker3, ticker4)
    #     markup1.row(ticker5, ticker6)
    #     markup1.row(btn1, btn_cancel)
    markup1.row(ticker1, ticker2, ticker3)
    markup1.row(ticker4, ticker5, ticker6)
    markup1.row(btn1, btn_cancel)
    state = dp.current_state(user=message.from_user.id)
    await state.set_state(TestStates.all()[1])
    return await message.reply(MESSAGES['get_tickers'], reply_markup=markup1)


@dp.message_handler(state='*', commands=['set_sum', 'Добавить_сумму'])
async def set_sum_command(message: types.Message):
    markup2 = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    state = dp.current_state(user=message.from_user.id)
    await state.set_state(TestStates.all()[2])
    return await message.reply(MESSAGES['get_sum'], reply_markup=markup2.add(btn2).add(btn_cancel))


@dp.message_handler(state='*', commands=['set_weights', 'Добавить_веса'])
async def set_weights_command(message: types.Message):
    markup3 = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    state = dp.current_state(user=message.from_user.id)
    await state.set_state(TestStates.all()[3])
    return await message.reply(MESSAGES['get_weights'] + f'\nКоличество весов, которые надо ввести: {len(tickers)}.',
                               reply_markup=markup3.add(btn3).add(btn_cancel))


@dp.message_handler(state='*', commands=['trade', 'Запустить_симуляцию'])
async def set_weights_command(message: types.Message):
    global weights, summa, tickers, portfolio_exists, portfolio
    weights = [float(i) for i in weights]
    if not portfolio_exists:
        portfolio = Portfolio(tickers=tickers, weights=weights, init_balance=float(summa),
                              strategy=get_decision_macd_conservative_strategy)

    try:
        for i in range(1):
            resp = await portfolio.call_strategy()
            if portfolio.flg_end_process:
                portfolio_exists = False
                break

            await message.reply(
                f'Баланс: {portfolio.full_balance:0.2f} | \n'
                f'{json.dumps(resp.get(), indent=4, ensure_ascii=False)}'
            )
    except Exception as e:
        print(e)
        portfolio = Portfolio(tickers=tickers, weights=weights, init_balance=float(summa),
                              strategy=get_decision_macd_conservative_strategy)


@dp.message_handler(state='*', commands=['cancel', 'Отмена'])
async def process_setstate_command(message: types.Message):
    global portfolio_exists

    portfolio_exists = False

    state = dp.current_state(user=message.from_user.id)
    await state.reset_state()

    return await message.reply(MESSAGES['state_reset'])


@dp.message_handler(state=TestStates.TEST_STATE_1)
async def first_test_state_case_met(message: types.Message):
    tickers.append(message.text)
    await message.reply(
        f"Тикеры записаны:{tickers}. \n\nЕсли хотите добавить тикер - введите его следующим сообщением. \n\nЧтобы продолжить введите \n/set_sum",
        reply=False, )


@dp.message_handler(state=TestStates.TEST_STATE_2[0])
async def second_test_state_case_met(message: types.Message):
    global summa
    summa = float(message.text)
    if summa < 0:
        summa = 0
        return await message.reply(f'Сумма меньше нуля. Введите неотрицательную сумму.', reply=False)

    else:
        return await message.reply(f'Сумма ({summa}) записана. \nТеперь распределим веса: /set_weights', reply=False)


@dp.message_handler(state=TestStates.TEST_STATE_3)
async def third_or_fourth_test_state_case_met(message: types.Message):
    global weights
    weights_spl = []
    weights.append(message.text)
    lst_number = []
    for i in range(0, len(weights)):
        weights_spl += weights[i].split(', ')
    float_weights = []
    for weight in weights_spl:
        float_weights.append(float(weight))

    lst_number = [x for x in float_weights if x < 0]

    if lst_number == []:
        if len(weights_spl) == len(tickers):
            if sum(float_weights) == 1:
                return await message.reply(f"Отлично! Веса записаны:{weights_spl}. \n\nЧтобы продолжить введите /trade",
                                           reply=False)
            else:
                weights = []
                weights_spl = []
                return await message.reply(
                    f"Сумма весов не равна 1. Список очищен, необходимо ввести веса заново. Сумма должна быть равна 1!",
                    reply=False)
        if len(weights_spl) < len(tickers):
            return await message.reply(
                f"Сейчас записаны веса:{weights_spl}. \n\nВам необходимо добавить еще {len(tickers) - len(weights_spl)}, чтобы приступить к следующему шагу",
                reply=False)
        if len(weights_spl) > len(tickers):
            weights = []
            weights_spl = []
            float_weights = []
            return await message.reply(f"Стоп! Весов больше, чем тикеров, список очищен, необходимо ввести веса заново",
                                       reply=False)
    else:
        weights = []
        weights_spl = []
        float_weights = []
        lst_number == []
        return await message.reply(f"Вы ввели значения меньше 0. Пожалуйста, вводите неотрицательные значения",
                                   reply=False)
        #     await message.reply(f"Веса записаны:{weights_spl}, {len(weights_spl), len(tickers)}", reply=False)


@dp.message_handler(state=TestStates.all())
async def some_test_state_case_met(message: types.Message):
    with dp.current_state(user=message.from_user.id) as state:
        text = MESSAGES['current_state'].format(
            current_state=await state.get_state(),
            states=TestStates.all()
        )
    await message.reply(text, reply=False)


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


import nest_asyncio

nest_asyncio.apply()

if __name__ == '__main__':
    executor.start_polling(dp, on_shutdown=shutdown)
