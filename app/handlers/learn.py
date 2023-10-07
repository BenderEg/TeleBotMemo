from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from congif import get_data, list_learning_pool, list_all_data
from models import FSMmodel


router: Router = Router()


@router.message(Command(commands='learn'), StateFilter(default_state))
async def process_training_command(message: Message, state: FSMContext):

    data: dict = await get_data(state, message.chat.id)
    if not data.get('objects', False):
        await message.answer(
            'Сначала необходимо внести объекты в базу данных.')
    else:
        learning_pool = list(filter(lambda x: x['n'] == 1, data['objects']))
        if learning_pool:
            res = await list_learning_pool(learning_pool)
            await message.answer(res, parse_mode='html')
        else:
            await message.answer(
                'Сегодня учить нечего, для вывода полного \
списка слов нажимите /list_all')


@router.message(Command(commands='list_all'), StateFilter(
        default_state, FSMmodel.add, FSMmodel.delete))
async def process_list_all_command(message: Message, state: FSMContext):
    data: dict = await get_data(state, message.chat.id)
    if not data.get('objects', False):
        await message.answer('В базе отсутсвуют объекты. \
Для добавления выберите команду /add')
    res = await list_all_data(data['objects'])
    if len(res) > 4096:
        for step in range(0, len(res), 4096):
            await message.answer(res[step:step+4096], parse_mode='html')
    await message.answer(res, parse_mode='html')
