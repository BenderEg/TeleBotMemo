from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery

from congif import get_user_categories, create_categories_list, \
    get_data, update_db
from models import FSMmodel, CategoryResponse, TextFilter

router: Router = Router()


@router.message(StateFilter(default_state, FSMmodel.choose_category),
                Command(commands='choose_category'))
async def process_choose_category_command(message: Message, state: FSMContext):
    categories = await get_user_categories(message)
    if categories:
        builder = await create_categories_list(categories)
        await get_data(state, message.chat.id)
        await state.update_data(categories=categories)
        await message.answer(
            text='Выберите категорию из списка.',
            reply_markup=builder.as_markup())
        await state.set_state(FSMmodel.choose_category)
    else:
        await message.answer(
            text='Создайте категорию выбрав команду /add_category.')


@router.message(StateFilter(FSMmodel.choose_category),
                Command(commands='cancel'))
async def process_exit_choose_category_mode_command(message: Message,
                                                    state: FSMContext):
    await message.answer('Вы вышли из режима выбора категории.')
    await state.set_state(state=None)


@router.message(StateFilter(FSMmodel.choose_category), Command(commands=(
        'training', 'learn', 'delete', 'add', 'add_category')))
async def proces_other_commands_press(message: Message):
    await message.answer(
            text='Сначала выйдите из режима \
выбора категории выбрав команду /cancel)'
        )


@router.message(StateFilter(FSMmodel.choose_category), TextFilter())
async def process_text(message: Message):
    await message.answer(
            text=('Текстовые сообщения не воспринимаются в \
режиме выбора категории. Для выхода из режима выберите команду /cancel')
                )


@router.callback_query(StateFilter(FSMmodel.choose_category),
                       CategoryResponse())
async def process_buttons_press(callback: CallbackQuery, state: FSMContext):
    data: dict = await get_data(state, callback.from_user.id)
    categories = data['categories']
    category = categories[int(callback.data)]
    await state.update_data(category=category)
    await callback.message.edit_text(
        text=f'Вы выбрали категорию <b>"{category}"</b>.\n\
Для дальейшей работы выберите комаду /add, /training или /learn.',
        parse_mode='html')
    await update_db(state, callback.from_user.id)
    await state.set_state(state=None)
