from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.state import default_state
from lexicon import LEXICON_RU
from models import *
from congif import *
from aiogram.fsm.context import FSMContext
from random import shuffle


router: Router = Router()


@router.message(Command(commands='training'), StateFilter(default_state))
async def process_training_command(message: Message, state: FSMContext):

    data: dict = await get_data(state, message.chat.id)
    training_data = list(filter(lambda x: x['diff'] <= 0, data['objects']))
    if training_data:
        shuffle(training_data)
        cur = 0
        await state.update_data(cur = cur, training_data=training_data)
        await message.answer(text=f'{training_data[cur]["object"]}\n -------------------\n<tg-spoiler>{training_data[cur]["meaning"]}</tg-spoiler>', \
                             reply_markup=builder.as_markup(), parse_mode='html')
        await state.set_state(FSMmodel.training)
    else:
        await message.answer(
            text='На сегодня нет объектов для тренировки, вы можете попробовать повторить \
новые объекты или объекты, которые пока плохо запомнились:).\n\
Для перехода в режим повторения нажмите /learn'
                )


@router.callback_query(StateFilter(FSMmodel.training), Response())
async def process_buttons_press(callback: CallbackQuery, state: FSMContext):
    data: dict = await get_data(state, callback.from_user.id)
    training_data = data['training_data']
    cur = int(data['cur'])
    training_data[cur]['grade'] = callback.data
    cur += 1
    if cur < len(training_data):
        await state.update_data(training_data=training_data, cur = cur)
        await callback.message.edit_text(text=f'{training_data[cur]["object"]}\n -------------------\n<tg-spoiler>{training_data[cur]["meaning"]}</tg-spoiler>', \
                                         reply_markup=callback.message.reply_markup, parse_mode='html')
    else:
        await state.update_data(training_data=training_data)
        await update_db(state, callback.message.chat.id)
        await callback.message.edit_text(text='Тренировка завершена. Данные обновлены.')
        await state.set_state(state=None)


@router.callback_query(StateFilter(FSMmodel.training), EndTraining())
async def process_end_training_press(callback: CallbackQuery, state: FSMContext):
    await update_db(state, callback.message.chat.id)
    await callback.message.edit_text(
        text=LEXICON_RU['/end_training']
    )
    await state.set_state(state=None)


@router.message(StateFilter(FSMmodel.training), Command(commands=('cancel')))
async def proces_text_press(message: Message, state: FSMContext):
    await update_db(state, message.chat.id)
    await message.answer(
        text=LEXICON_RU['/end_training']
    )
    await state.set_state(state=None)


@router.message(StateFilter(FSMmodel.training), Command(commands=('add', 'learn', 'delete')))
async def proces_text_press(message: Message):
    await message.answer(
            text='Сначала завершить тренировку (нажмите "End training" или выберите команду /cancel)'
        )


@router.message(StateFilter(FSMmodel.training))
async def proces_text_press(message: Message):
    await message.answer(
            text='Вы находитесь в режиме тренировки, для завершения нажмите "End training" или выберите команду /cancel'
        )