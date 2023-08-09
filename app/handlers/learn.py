from aiogram import Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message
from aiogram.fsm.state import default_state
from lexicon import LEXICON_RU
from models import *
from congif import *
from aiogram.fsm.context import FSMContext

router: Router = Router()


@router.message(Command(commands='learn'), StateFilter(default_state, FSMmodel.delete))
async def process_training_command(message: Message, state: FSMContext):

    data = await get_data_cash(state)
    if not data:
        data = await get_data_db(message.chat.id, state)
    if data:
        learning_pool = list(filter(lambda x: x['n'] == 1, data))
        if learning_pool:
            res = list_learning_pool(learning_pool)
            await message.answer(res, parse_mode='html')
        else:
            await message.answer('Сегодня учить нечего, для вывода полного списка слов нажимите /list_all')
    else:
        await message.answer('Сначала необходимо внести объекты в базу данных.')

@router.message(Command(commands='list_all'), StateFilter(default_state, FSMmodel.add, FSMmodel.delete))
async def process_list_all_command(message: Message, state: FSMContext):
    data = await get_data_cash(state)
    if not data:
        data = await get_data_db(message.chat.id, state)
    if data:
        res = list_all_data(data)
        await message.answer(res)
    else:
        await message.answer('В базе отсутсвуют объекты. Для добавления выберите команду /add')