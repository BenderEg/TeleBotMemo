from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery

from core.dependencies import del_service
from models.filters import TextFilter, UuidFilter
from models.exeptions import ServerErrorExeption
from models.system import FSMmodel

router: Router = Router()


@router.message(StateFilter(default_state), Command(commands='delete'))
async def process_del_enter_command(message: Message,
                                    state: FSMContext,
                                    service: del_service):
    user_id = message.from_user.id
    try:
        data: dict = await service.get_data(user_id, state)
        category: str = data.get('category')
        category_name = category if category else 'Все категории'
        if data.get('objects'):
            await message.answer(
            text=f'Вы в режиме удаления объекта из базы.\n\
Текущая категория: <b>"{category_name.capitalize()}"</b>.\n\
Введите наименование объекта.\n\
Для выхода из режима удаления нажмите /cancel.\n\
Для смены категории нажмите /choose_category',
            parse_mode='html')
            await state.set_state(FSMmodel.delete)
        else:
            await message.answer(
                text='Нечего удалять из системы.\n\
Для добавления объектов выберите категорию нажав /choose_category.')
    except ServerErrorExeption as err:
        await message.answer(text=err.msg)
        await state.clear()


@router.message(StateFilter(FSMmodel.delete), Command(commands='cancel'))
async def process_exit_del_mode_command(message: Message,
                                        state: FSMContext,
                                        service: del_service):
    user_id = message.from_user.id
    try:
        data = await service.get_data(user_id, state)
        objects, categories = await service.update_db(user_id, data)
        await service.update_state(objects, categories, state)
        await state.set_state(state=None)
        await message.answer('Вы вышли из режима удаления объекта.')
    except ServerErrorExeption as err:
        await message.answer(text=err.msg)
        await state.clear()


@router.message(StateFilter(FSMmodel.delete), Command(commands='delete'))
async def process_del_in_progress_command(message: Message):
    await message.answer('Вы уже в режиме удаления объекта.\n\
Введите наименование объекта.\n\
Для выхода из режима ввода нажмите /cancel.')


@router.message(StateFilter(FSMmodel.delete), Command(
        commands=('training', 'learn', 'add',
                  'choose_category', 'add_category')))
async def proces_text_press(message: Message):
    await message.answer(
            text='Сначала выйдите из режима \
удаления объектов выбрав команду /cancel.'
        )


@router.message(StateFilter(FSMmodel.delete), TextFilter())
async def process_del_command(message: Message,
                              text: str,
                              state: FSMContext,
                              service: del_service):
    user_id = message.from_user.id
    try:
        data: dict = await service.get_data(user_id, state)
        filtered_objects = list(filter(lambda x: x['object'].find(
            text.lower()) != -1, data['objects']))
        if filtered_objects:
            del_builder = service.create_delete_builder(filtered_objects)
            await message.answer(
                text='Нажмите для подтверждения \
удаления на объект. \n\
Нажмите /cancel для выхода из режима удаления.',
                reply_markup=del_builder.as_markup())
        else:
            await message.answer(text=f"Объект отсутствует в базе \
(категория '{data.get('category').capitalize()}').")
    except ServerErrorExeption as err:
        await message.answer(text=err.msg)
        await state.clear()


@router.callback_query(StateFilter(FSMmodel.delete), UuidFilter())
async def process_buttons_press(callback: CallbackQuery,
                                value: str,
                                state: FSMContext,
                                service: del_service):
    user_id = callback.from_user.id
    try:
        data: dict = await service.get_data(user_id, state)
        deleted_objects: list = data.get('deleted_objects')
        deleted_objects.append(value)
        deleted_item, objects = service.filter_objects(
            data.get('objects'), value)
        await state.update_data(deleted_objects=deleted_objects,
                                objects=objects)
        await callback.message.edit_text(
            text=f'Выбранный объект: {deleted_item["object"]} = {deleted_item["meaning"]}.\n\
помечен на удаление. Для сохранения изменений и выхода из режима \
удаления нажмите /cancel или введите наименование \
следующего объекта для удаления.')
    except ServerErrorExeption as err:
        await callback.message.edit_text(text=err.msg)
        await state.clear()
