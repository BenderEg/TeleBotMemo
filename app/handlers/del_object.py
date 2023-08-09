from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.state import default_state
from lexicon import LEXICON_RU
from models import *
from congif import *
from aiogram.fsm.context import FSMContext
from aiogram.methods import DeleteMessage


router: Router = Router()


@router.message(Command(commands='delete'))
async def process_del_enter_command(message: Message, state: FSMContext):
    data = await get_data_cash(state)
    if not data:
        data = await get_data_db(message.chat.id, state)
        if not data:
            await message.answer(
        text='Нечего удалять из системы.\n\
Для добавления объектов нажмите /add')
    await state.update_data(deleted_objects = [])
    await message.answer(
        text='Вы в режиме удаления объекта из базы. \n\
Введите наименование объекта.\n\
Для выхода из режима ввода нажмите /cancel')
    await state.set_state(FSMmodel.delete)


@router.message(StateFilter(FSMmodel.delete), Command(commands='cancel'))
async def process_exit_del_mode_command(message: Message, state: FSMContext):
    await del_values_db(state, message.chat.id)
    await message.answer('Вы вышли из режима удаления объекта.')


@router.message(StateFilter(FSMmodel.delete), Command(commands='delete'))
async def process_del_in_progress_command(message: Message, state: FSMContext):
    await message.answer('Вы уже в режиме удаления объекта.\n\
Введите наименование объекта.\n\
Для выхода из режима ввода нажмите /cancel')


@router.message(StateFilter(FSMmodel.delete), TextFilter())
async def process_del_command(message: Message, state: FSMContext):
    data = await get_data_cash(state)
    filtered_objects = list(filter(lambda x: x['object'].find(message.text) != -1, data))
    if len(filtered_objects) > 0:
        await state.update_data(filtered_objects = filtered_objects)
        del_builder = InlineKeyboardBuilder()
        for i, ele in enumerate(filtered_objects):
            del_builder.button(text=f"{ele['object']} = {ele['meaning']}", callback_data=f"{i}")
        del_builder.adjust(1)
        await message.answer(text='Нажмите для подтверждения удаления на объект.', \
                             reply_markup=del_builder.as_markup())
    else:
        await message.answer(text='Объект отсутствует в базе.')


@router.callback_query(StateFilter(FSMmodel.delete), DigitResponse())
async def process_buttons_press(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    filtered_objects: list = data['filtered_objects']
    deleted_objects: list = data['deleted_objects']
    num: int = int(callback.data)
    if 0 <= num < len(filtered_objects):
        cur = filtered_objects[num]
        deleted_objects.append(cur['object'])
        objects = list(filter(lambda x: x['object'] != cur['object'], data['objects']))
        await state.update_data(deleted_objects=deleted_objects, objects=objects)
        await callback.message.edit_text(text=f'Объект: {cur["object"]} = {cur["meaning"]}.\n\
помечен на удаление. Для сохранения изменений и выхода из режема удаления нажмите /cancel или введите наименование следующего объекта для удаления.')
    else:
        await callback.answer(text='Произошла ошибка. Для перезагрузки нажмите /cancel')