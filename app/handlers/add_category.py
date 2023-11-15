from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message
from sqlalchemy.exc import IntegrityError

from core.dependencies import category_service
from core.logger import logging
from models.filters import TextFilter
from models.exeptions import ServerErrorExeption
from models.system import FSMmodel


router: Router = Router()


@router.message(StateFilter(default_state), Command(commands='add_category'))
async def process_add_category_command(message: Message, state: FSMContext):
    await message.answer(
        text='Введите наименование категории.')
    await state.set_state(FSMmodel.add_category)


@router.message(StateFilter(FSMmodel.add_category), Command(commands='cancel'))
async def process_exit_add_category_mode_command(message: Message,
                                                 state: FSMContext):
    await message.answer('Вы вышли из режима создания категории.')
    await state.set_state(state=None)


@router.message(StateFilter(FSMmodel.add_category), Command(commands=(
        'training', 'learn', 'delete', 'add', 'choose_category')))
async def proces_other_commands_press(message: Message):
    await message.answer(
            text='Сначала выйдите из режима \
создания категории выбрав команду /cancel.'
        )


@router.message(StateFilter(FSMmodel.add_category), Command(
        commands='add_category'))
async def process_add_category_in_progress_command(message: Message):
    await message.answer('Вы уже в режиме создания категории.\n\
Введите наименование категории.\n\
Для сохранения данных и выхода из режима создания категории нажмите /cancel')


@router.message(StateFilter(FSMmodel.add_category), TextFilter())
async def process_new_category_command(message: Message,
                                       text: str,
                                       state: FSMContext,
                                       service: category_service):
    user_id = message.from_user.id
    text = text.lower()
    if text == 'все категории':
        logging.warning(f"Категория '{text}' введена пользователем: {user_id}")
        await message.answer('Недопустимое имя. \
Придумайте другое наименование категории. Для выхода из режима \
создания категории нажмите /cancel')
    else:
        try:
            await service.add_category(user_id, text)
            await state.update_data(category=text)
            data = await service.get_data(user_id, state)
            objects, categories = await service.update_db(user_id, data)
            await service.update_state(objects, categories, state)
            await state.set_state(state=None)
            await message.answer(f'Категория доступна в меню.\n\
Вы вышли из режима создания категории.\n\
Текущая категория <b>"{text}"</b>.', parse_mode='html')
        except IntegrityError as err:
            logging.error(f"Категория '{text}' уже существует у пользователя: {user_id}")
            await message.answer(text='Категория уже представлена в базе.\n\
Введите другое именование. Для просмотра категорий выйдите из режима (/cancel) и нажмите /choose_category.\n\
Если у вас нет категорий, нажмите /start, чтобы проверить наличие пользователя в системе.')
        except ServerErrorExeption as err:
            await message.answer(text=err.msg)
            await state.clear()
