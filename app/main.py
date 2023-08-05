from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message

from db_code import db_close, db_open
from congif import Response, list_all_data, treat_object_list, builder, Limit, update_objects, update_db, BOT_TOKEN, storage, EndTraining
from random import choice

bot: Bot = Bot(BOT_TOKEN)
dp: Dispatcher = Dispatcher(storage=storage)

user_dict: dict[int, dict[str, str | int | bool]] = {}


class FSMmodel(StatesGroup):
    # Создаем экземпляры класса State, последовательно
    # перечисляя возможные состояния, в которых будет находиться
    # бот в разные моменты взаимодейтсвия с пользователем
    training = State()        # Состояние тренировки


@dp.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):
    await message.answer(text='Этот бот помогает запоминать\n\n'
                              'Чтобы узнать больше о функционале - '
                              'отправьте команду /help')


@dp.message(Command(commands='help'))
async def process_help_command(message: Message):
    await message.answer(text='Перечень доступных команд:\n\
5 - perfect response\n\
4 - correct response after a hesitation\n\
3 - correct response recalled with serious difficulty\n\
2 - incorrect response; where the correct one seemed easy to recall\n\
1 - incorrect response; the correct one remembered\n\
0 - complete blackout.'
    )

@dp.message(Command(commands='list_all'), StateFilter(default_state))
async def process_list_all_command(message: Message):
    con, cur = db_open()
    cur.execute('SELECT object, meaning FROM bank WHERE user_id = %s ORDER BY object', (message.chat.id,))
    response = cur.fetchall()
    db_close(con)
    res = list_all_data(response)
    await message.answer(res)

@dp.message(Command(commands='training'))
async def process_training_command(message: Message, state: FSMContext):
    con, cur = db_open()
    cur.execute('SELECT object, meaning, e_factor, interval, n, case when object is \
                not NULL then -1 else -2 end as grade FROM bank WHERE user_id = %s ORDER BY next_date - now()::date \
                LIMIT %s', (message.chat.id, Limit))
    await state.update_data(objects = cur.fetchall())
    db_close(con)
    data = await state.get_data()
    if data["objects"]:
        cur = choice(data["objects"])
        await state.update_data(cur = cur)
        await message.answer(text=f'{cur["object"]}\n -------------------\n<tg-spoiler>{cur["meaning"]}</tg-spoiler>', reply_markup=builder.as_markup(), parse_mode='html')
        await state.set_state(FSMmodel.training)

@dp.callback_query(StateFilter(FSMmodel.training), Response())
async def process_buttons_press(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    objects = [update_objects(ele, data['cur'], callback) for ele in data['objects']]
    res = treat_object_list(objects)
    if res:
        cur = choice(res)
        await state.update_data(cur = cur, objects=objects)
        await callback.message.edit_text(text=f'{cur["object"]}\n -------------------\n<tg-spoiler>{cur["meaning"]}</tg-spoiler>', reply_markup=callback.message.reply_markup, parse_mode='html')
    else:
        await state.update_data(objects=objects)
        await update_db(state, callback.message.chat.id)
        await bot.send_message(chat_id=callback.message.chat.id, text='End of a training')
        await state.clear()


@dp.callback_query(StateFilter(FSMmodel.training), EndTraining())
async def process_end_training_press(callback: CallbackQuery, state: FSMContext):
    await update_db(state, callback.message.chat.id)
    await bot.send_message(chat_id=callback.message.chat.id, text='End of a training')
    await state.clear()


if __name__ == '__main__':
    dp.run_polling(bot)