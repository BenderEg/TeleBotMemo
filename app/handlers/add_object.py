from os import path

from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message
from sqlalchemy.exc import IntegrityError

from core.dependencies import add_service, csv_service
from models2.filters import FileFilter, TextFilter
from models import FSMmodel, FileHandler

router: Router = Router()


@router.message(StateFilter(default_state), Command(commands='add'))
async def process_add_command(message: Message,
                              state: FSMContext,
                              service: add_service):
    user_id = message.chat.id
    data: dict = await service.get_data(user_id, state)
    category = data.get('category')
    if category and category != 'Все категории':
        await message.answer(
            text=f'Вы в режиме добавление объектов в базу. \n\
Текущая категория <b>"{category}"</b>.\n\
Для смены категории выберите /choose_category.\n\
Введите объект в формате: ключ = значение.\n\
Для выхода из режима ввода и сохранения данных нажмите /cancel.',
            parse_mode='html')
        await state.set_state(FSMmodel.add)
    else:
        await message.answer(text="Категория не выбрана.\n\
Для продолжения работы выберите /choose_category или /add_category.\n\
В режиме 'Все категории' команда /add не доступна.")


@router.message(StateFilter(FSMmodel.add), Command(commands='cancel'))
async def process_exit_add_mode_command(message: Message,
                                        state: FSMContext,
                                        service: add_service):
    user_id = message.from_user.id
    await service.add_values_db(user_id, state)
    await message.answer('Вы вышли из режима ввода объекта.')
    await state.clear()


@router.message(StateFilter(FSMmodel.add), Command(commands=(
        'training', 'learn', 'delete', 'add_category', 'choose_category')))
async def proces_text_press(message: Message):
    await message.answer(
            text='Сначала выйдите из режима \
добавление объектов выбрав команду /cancel.'
        )


@router.message(StateFilter(FSMmodel.add), Command(commands='add'))
async def process_add_in_progress_command(message: Message):
    await message.answer('Вы уже в режиме ввода.\n\
Введите объект в формате: ключ = значение.\n\
Для сохранения данных и выхода из режима ввода нажмите /cancel.')


@router.message(StateFilter(FSMmodel.add), FileFilter())
async def add_from_file(message: Message, state: FSMContext,
                        name: str,
                        service: csv_service):
    user_id = message.chat.id
    data: dict = await service.get_data(user_id, state)
    category = data['category']
    with FileHandler(user_id, name) as dest:
        file = message.document
        await file.bot.download(file=file, destination=path.join(dest, name))
        data: list = service.read_data_csv(path.join(dest, name))
        if data:
            try:
                await service.add_data_to_db(data, user_id, category)
                res: str = service.list_added_objects(data)
                await message.answer(
                    f'Объекты добавлены в базу:\n{res}', parse_mode='html')
                await state.clear()
            except IntegrityError:
                await message.answer('Произошла ошибка, проверьте, \
что файл с объектами заполнен корректно и не содержит уже присутствующих \
в перечне категории объектов.')


@router.message(StateFilter(FSMmodel.add), TextFilter())
async def process_new_entity_command(message: Message,
                                     state: FSMContext,
                                     text: str,
                                     service: add_service):
    user_id = message.from_user.id
    try:
        value = service.parse_add_value(text)
        if value:
            data: dict = await service.get_data(user_id, state)
            value['category'] = data['category']
            add_objects: list = data.get('add_objects', [])
            objects: list = data.get('objects', [])
            if any(map(
                lambda x: True if x.get('object') == value['object'] else False,
                    (objects))):
                await message.answer('Объект уже есть в базе.')
            else:
                objects.append(value)
                add_objects.append(value)
                await state.update_data(add_objects=add_objects,
                                        objects=objects)
                await message.answer('Объект принят.\n\
Для сохранения данных и выхода из режима ввода нажмите /cancel.')
    except ValueError:
        await message.answer(text=('Значение некорректно. \
Введите объект в формате: ключ = значение. \
Для выхода из режима ввода нажмите /cancel.'))
