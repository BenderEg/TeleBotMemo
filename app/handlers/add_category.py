from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message
from sqlalchemy.exc import IntegrityError

from core.dependencies import category_service, data_service
from models import FSMmodel, TextFilter

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
создания категории выбрав команду /cancel)'
        )


@router.message(StateFilter(FSMmodel.add_category), Command(
        commands='add_category'))
async def process_add_category_in_progress_command(message: Message):
    await message.answer('Вы уже в режиме создания категории.\n\
Введите наименование категории.\n\
Для сохранения данных и выхода из режима создания категории нажмите /cancel')


@router.message(StateFilter(FSMmodel.add_category), TextFilter())
async def process_new_category_command(message: Message,
                                       state: FSMContext,
                                       category_service: category_service,
                                       data_service: data_service):
    name = message.text
    user_id = message.from_user.id
    if name == 'Все категории':
        await message.answer('Недопустимое имя. \
Придумайте другое наименование категории. Для выхода из режима \
создания категории нажмите /cancel')
    else:
        try:
            await category_service.add_category(user_id, name)
            await state.clear()
            await message.answer(f'Категория доступна в меню.\n\
Вы вышли из режима создания категории.\n\
Текущая категория <b>"{message.text}"</b>.', parse_mode='html')
            await data_service.get_data(user_id, state)
            await state.update_data(category=name)
            await data_service.update_db(user_id, state)
        except IntegrityError:
            await message.answer(text='Категория уже представлена в базе.\n\
Введите другое именование. Для просмотра категорий выйдите из режима (/cancel) и нажмите /choose_category.')
