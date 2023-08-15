from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from lexicon import LEXICON_RU
from models import *
from congif import *
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state


router: Router = Router()


@router.message(StateFilter(default_state), Command(commands='add'))
async def process_add_command(message: Message, state: FSMContext):
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


@router.message(StateFilter(FSMmodel.add), Command(commands=('training', 'learn', 'delete')))
async def proces_text_press(message: Message):
    await message.answer(
            text='Сначала выйдите из режима добавление объектов выберав команду /cancel)'
        )


@router.message(StateFilter(FSMmodel.add), Command(commands='add'))
async def process_add_in_progress_command(message: Message):
    await message.answer('Вы уже в режиме ввода.\n\
Введите объект в формате: ключ = значение.\n\
Для сохранения данных и выхода из режима ввода нажмите /cancel')


@router.message(StateFilter(FSMmodel.add), FileFilter())
async def add_from_file(message: Message, state: FSMContext, name: str):
    data: list = await read_data_csv(name)
    await write_to_db_from_csv(message.chat.id, data)
    res: str = await list_added_objects(data)
    if res:
        await message.answer(f'Объекты добавлены в базу:\n{res}', parse_mode='html')
        await state.set_state(state=None)
    else:
        await message.answer(f'Произошла ошибка, проверьте, что файл с объектами заполнен корректно.')


@router.message(StateFilter(FSMmodel.add), TextFilter())
async def process_new_entity_command(message: Message, state: FSMContext):
    value = await parse_add_value(message)
    if value:
        data: dict = await get_data(state, message.chat.id)
        add_objects: list = data.get('add_objects', [])
        objects: list = data.get('objects', [])
        if any(map(lambda x: True if x.get('object') == value['object'] else False, (objects))):
            await message.answer('Объект уже есть в базе.')
        else:
            print('я в режиме принятия объектов')
            print(value)
            objects.append(value)
            add_objects.append(value)
            await state.update_data(add_objects=add_objects, objects=objects)
            await message.answer('Объект принят.\n\
Для сохранения данных и выхода из режима ввода нажмите /cancel')