from random import shuffle

from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message

from core.dependencies import learning_service
from lexicon import LEXICON_RU
from models import builder, FSMmodel, Response, CallbackQuery, EndTraining

router: Router = Router()


@router.message(Command(commands='training'), StateFilter(default_state))
async def process_training_command(message: Message,
                                   state: FSMContext,
                                   service: learning_service):
    user_id = message.from_user.id
    data: dict = await service.get_data(user_id, state)
    category = data['category']
    category_name = category if category else 'Все категории'
    training_data = list(filter(lambda x: x['diff'] <= 0, data['objects']))
    if training_data:
        shuffle(training_data)
        cur = 0
        await state.update_data(cur=cur, training_data=training_data)
        text_response = service.prepare_text_response(training_data[cur])
        await message.answer(text=text_response,
                             reply_markup=builder.as_markup(),
                             parse_mode='html')
        await state.set_state(FSMmodel.training)
    else:
        await message.answer(
            text=f'На сегодня нет объектов для тренировки \
в выбранной категории: <b>"{category_name}"</b>, \n\
вы можете попробовать повторить \n\
новые объекты или объекты, которые пока плохо запомнились:).\n\
Для перехода в режим повторения нажмите /learn', parse_mode='html'
                )


@router.callback_query(StateFilter(FSMmodel.training), Response())
async def process_buttons_press(callback: CallbackQuery,
                                state: FSMContext,
                                service: learning_service):
    user_id = callback.from_user.id
    data: dict = await service.get_data(user_id, state)
    training_data = data['training_data']
    if training_data:
        try:
            cur = int(data['cur'])
            training_data[cur]['grade'] = callback.data
            cur += 1
            if cur < len(training_data):
                await state.update_data(training_data=training_data, cur=cur)
                text_response = service.prepare_text_response(training_data[cur])
                await callback.message.edit_text(
                    text=text_response,
                    reply_markup=callback.message.reply_markup,
                    parse_mode='html')
            else:
                await state.update_data(training_data=training_data)
                await service.update_db(user_id, state)
                await callback.message.edit_text(
                    text='Тренировка завершена. Данные обновлены.')
                await state.set_state(state=None)
        except:
            await callback.message.edit_text(
                text='Тренировка была атоматически завершена. \
Для продолжения нажмите /training. From exeption.')
            await state.clear()
    else:
        await callback.message.edit_text(
            text='Тренировка была атоматически завершена. \
Для продолжения нажмите /training.')
        await state.clear()


@router.callback_query(StateFilter(FSMmodel.training), EndTraining())
async def process_end_training_press(callback: CallbackQuery,
                                     state: FSMContext,
                                     service: learning_service):
    user_id = callback.from_user.id
    await service.update_db(user_id, state)
    await callback.message.edit_text(
        text=LEXICON_RU['/end_training']
    )
    await state.set_state(state=None)


@router.message(StateFilter(FSMmodel.training),
                Command(commands=('cancel')))
async def proces_cancel_command(message: Message,
                                state: FSMContext,
                                service: learning_service):
    user_id = message.from_user.id
    await service.update_db(user_id, state)
    await message.answer(
        text=LEXICON_RU['/end_training']
    )
    await state.set_state(state=None)


@router.message(StateFilter(FSMmodel.training),
                Command(commands=('add', 'learn', 'delete',
                                  'add_category', 'choose_category',
                                  'list_all')))
async def proces_some_commands(message: Message):
    await message.answer(
            text='Сначала завершить тренировку \
(нажмите "End training" или выберите команду /cancel.)'
        )


@router.message(StateFilter(FSMmodel.training))
async def proces_text_press(message: Message):
    await message.answer(
            text='Вы находитесь в режиме тренировки, для завершения \
нажмите "End training" или выберите команду /cancel.'
                )
