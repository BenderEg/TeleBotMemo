from os import path

from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message
from sqlalchemy.exc import IntegrityError

from core.dependencies import add_service, csv_service
from core.logger import logging
from models.filters import FileFilter, TextFilter
from models.exeptions import ServerErrorExeption, CsvReadExeption
from models.system import FSMmodel, FileHandler

router: Router = Router()


@router.message(StateFilter(default_state), Command(commands='add'))
async def process_add_command(message: Message,
                              state: FSMContext,
                              service: add_service):
    user_id = message.chat.id
    try:
        data: dict = await service.get_data(user_id, state)
        category: str = data.get('category')
        if category and category != 'Все категории':
            await message.answer(text=f'Вы в режиме добавление объектов в базу. \n\
Текущая категория <b>"{category.capitalize()}"</b>.\n\
Для смены категории выберите /choose_category.\n\
Введите объект в формате: ключ = значение.\n\
Для выхода из режима ввода и сохранения данных нажмите /cancel.',
                                 parse_mode='html')
            await state.set_state(FSMmodel.add)
        else:
            await message.answer(text="Категория не выбрана.\n\
Для продолжения работы выберите /choose_category или /add_category.\n\
В режиме 'Все категории' команда /add не доступна.")
    except ServerErrorExeption as err:
        await message.answer(text=err.msg)
        await state.clear()



@router.message(StateFilter(FSMmodel.add), Command(commands='cancel'))
async def process_exit_add_mode_command(message: Message,
                                        state: FSMContext,
                                        service: add_service):
    user_id = message.from_user.id
    try:
        data = await service.get_data(user_id, state)
        objects, categories = await service.update_db(user_id, data)
        await service.update_state(objects, categories, state)
        await state.set_state(state=None)
        await message.answer('Вы вышли из режима ввода объекта.')
    except ServerErrorExeption as err:
        await message.answer(text=err.msg)
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
    try:
        data: dict = await service.get_data(user_id, state)
        category = data['category']
        with FileHandler(user_id, name) as dest:
            file = message.document
            await file.bot.download(file=file, destination=path.join(dest, name))
            data_from_file: list = service.read_data_csv(path.join(dest, name))
            if data_from_file:
                await service.add_data_to_db(data_from_file, user_id, category)
                res: str = service.list_added_objects(data_from_file)
                await message.answer(
                    f'Объекты добавлены в базу:\n{res}\n\
Вы вышли из выбранного режима и категории. Для продолжения работы \
рекомендуется выбрать категорию /choose_category.',
                    parse_mode='html')
                await state.clear()
    except CsvReadExeption as err:
        logging.error(f'{err.msg} у пользователя: {user_id}')
        await message.answer('Файл некорректный. Проверьте файл!')
    except ValueError:
        logging.error(f'Ошибка ввода данных у пользователя: {user_id}')
        await message.answer('Ошибка в данных. Проверьте данные!')
    except IntegrityError:
        logging.error(f'Ошибка записи из файла для пользователя: {user_id}')
        await message.answer('Произошла ошибка, проверьте, \
что файл с объектами заполнен корректно и не содержит уже присутствующих \
в перечне категории объектов.')
    except ServerErrorExeption as err:
        await message.answer(text=err.msg)
        await state.clear()

@router.message(StateFilter(FSMmodel.add), TextFilter())
async def process_new_entity_command(message: Message,
                                     state: FSMContext,
                                     text: str,
                                     service: add_service):
    user_id = message.from_user.id
    try:
        data: dict = await service.get_data(user_id, state)
        category = data.get('category')
        if not category:
            await message.answer('Выберите категорию нажав /choose_category.')
        else:
            value = service.parse_add_value(text)
            if value:
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
        logging.error(f'Ошибка ввода объекта для пользователя: {user_id}')
        await message.answer(text=('Значение некорректно. \
Введите объект в формате: ключ = значение. \
Для выхода из режима ввода нажмите /cancel.'))
    except ServerErrorExeption as err:
        await message.answer(text=err.msg)
        await state.clear()