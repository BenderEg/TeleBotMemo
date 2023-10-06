from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message

from congif import add_category_db, update_db, get_data
from models import FSMmodel, TextFilter, redis

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
async def process_new_category_command(message: Message, state: FSMContext):
    await add_category_db(message, state)
    await get_data(state, message.chat.id)
    await state.update_data(category=message.text)
    await update_db(state, message.chat.id)
    await message.answer(f'Категория доступна в меню.\n\
Для выбора категории нажмите /choose_сategory.\n\
Вы вышли из режима создания категории.\n\
Текущая категория <b>"{message.text}"</b>.', parse_mode='html')
