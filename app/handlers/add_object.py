from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.state import default_state
from lexicon import LEXICON_RU
from models import *
from congif import *
from aiogram.fsm.context import FSMContext


router: Router = Router()


@router.message(Command(commands='add'))
async def process_add_command(message: Message, state: FSMContext):
    data = await get_data_cash(state)
    if not data:
        data = await get_data_db(message.chat.id, state)
    await state.update_data(add_objects = [])
    await message.answer(
        text='Вы в режиме добавление объектов в базу. \n\
Введите объект в формате: ключ = значение.\n\
Для выхода из режима ввода и сохранения данных нажмите /cancel')
    await state.set_state(FSMmodel.add)


@router.message(StateFilter(FSMmodel.add), Command(commands='cancel'))
async def process_exit_add_mode_command(message: Message, state: FSMContext):
    await add_values_db(state, message.chat.id)
    await message.answer('Вы вышли из режима ввода объекта.')
    await state.set_state(state=None)


@router.message(StateFilter(FSMmodel.add), Command(commands='add'))
async def process_add_in_progress_command(message: Message):
    await message.answer('Вы уже в режиме ввода.\n\
Введите объект в формате: ключ = значение.\n\
Для сохранения данных и выхода из режима ввода нажмите /cancel')


@router.message(StateFilter(FSMmodel.add), TextFilter())
async def process_new_entity_command(message: Message, state: FSMContext):
    value = await parse_add_value(message)
    if value:
        data = await state.get_data()
        objects: list = data['objects']
        add_objects: list = data['add_objects']
        if any(map(lambda x: True if x.get('object') == value['object'] else False, (objects))):
            await message.answer('Объект уже есть в базе.')
        else:
            objects.append(value)
            add_objects.append(value)
            await state.update_data(add_objects=add_objects, objects=objects)
            await message.answer('Объект принят.\n\
Для сохранения данных и выхода из режима ввода нажмите /cancel')
