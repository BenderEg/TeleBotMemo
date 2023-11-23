from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery

from core.dependencies import category_service
from models.filters import TextFilter, CategoryResponse
from models.exeptions import ServerErrorExeption
from models.system import FSMmodel

router: Router = Router()


@router.message(StateFilter(default_state,
                            FSMmodel.add,
                            FSMmodel.add_category,
                            FSMmodel.delete),
                Command(commands='choose_category'))
async def process_choose_category_command(message: Message,
                                          state: FSMContext,
                                          service: category_service):
    user_id = message.from_user.id
    try:
        data: dict = await service.get_data(user_id, state)
        categories: str = data.get('categories')
        if categories:
            builder = service.create_categories_list(categories)
            await message.answer(
                text='Выберите категорию из списка.',
                reply_markup=builder.as_markup())
            await state.set_state(FSMmodel.choose_category)
        else:
            await message.answer(
                text='Создайте категорию выбрав команду /add_category.')
    except ServerErrorExeption as err:
        await message.answer(text=err.msg)
        await state.clear()


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
выбора категории выбрав команду /cancel.'
        )


@router.message(StateFilter(FSMmodel.choose_category), TextFilter())
async def process_text(message: Message):
    await message.answer(
            text=('Текстовые сообщения не воспринимаются в \
режиме выбора категории. Для выхода из режима выберите команду /cancel.')
                )


@router.callback_query(StateFilter(FSMmodel.choose_category),
                       CategoryResponse())
async def process_buttons_press(callback: CallbackQuery,
                                text: str,
                                state: FSMContext,
                                service: category_service):
    user_id = callback.from_user.id
    try:
        category = None if text == 'Все категории' else text
        await state.set_state(state=None)
        await state.update_data(category=category)
        data = await service.get_data(user_id, state)
        objects, categories = await service.update_db(user_id, data)
        await service.update_state(objects, categories, state)
        if text == 'Все категории':
            await callback.message.edit_text(
                text=f'Вы выбрали категорию <b>"{text.capitalize()}"</b>.\n\
Для дальнейшей работы выберите комаду /delete, /training, /list_all или /learn.',
                parse_mode='html')
        else:
            await callback.message.edit_text(
                text=f'Вы выбрали категорию <b>"{text.capitalize()}"</b>.\n\
Для дальнейшей работы выберите комаду /add, /delete, /training, /list_all или /learn.',
                parse_mode='html')
    except ServerErrorExeption as err:
        await callback.message.edit_text(text=err.msg)
        await state.clear()
