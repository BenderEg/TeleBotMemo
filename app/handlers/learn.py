from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from core.dependencies import learning_service
from models.exeptions import ServerErrorExeption
from models.system import FSMmodel

router: Router = Router()


@router.message(Command(commands='learn'), StateFilter(default_state))
async def process_training_command(message: Message,
                                   state: FSMContext,
                                   service: learning_service):
    try:
        user_id = message.from_user.id
        data: dict = await service.get_data(user_id, state)
        if not data.get('objects'):
            await message.answer(
'Сначала необходимо внести объекты в базу данных.')
        else:
            learning_pool = list(filter(lambda x: x['n'] == 1, data['objects']))
            if learning_pool:
                res = service.list_learning_pool(learning_pool)
                await service.message_paginator(res, message)
            else:
                await message.answer(
'Сегодня учить нечего, для вывода полного \
списка слов нажимите /list_all.')
    except ServerErrorExeption as err:
        await message.answer(text=err.msg)
        await state.clear()


@router.message(Command(commands='list_all'), StateFilter(
        default_state, FSMmodel.add, FSMmodel.delete))
async def process_list_all_command(message: Message,
                                   state: FSMContext,
                                   service: learning_service):
    user_id = message.from_user.id
    try:
        data: dict = await service.get_data(user_id, state)
        if not data.get('objects'):
            await message.answer('В базе отсутствуют объекты. \
    Для добавления выберите команду /add.')
        res = service.list_all_data(data['objects'])
        await service.message_paginator(res, message)
    except ServerErrorExeption as err:
        await message.answer(text=err.msg)
        await state.clear()