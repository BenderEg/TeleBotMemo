from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message
from db_code import db_close, db_open
from congif import *
from models import *
from random import shuffle

bot: Bot = Bot(BOT_TOKEN)
dp: Dispatcher = Dispatcher(storage=storage)


@dp.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):
    await message.answer(text='Этот бот помогает запоминать\n'
                              'Чтобы узнать больше о функционале\n'
                              'отправьте команду /help')


@dp.message(Command(commands='help'))
async def process_help_command(message: Message):
    await message.answer(text='Перечень доступных команд:\n\
/start - \n\
/list_all - \n\
/add - \n\
/training - \n\
/learn - \n\
/cancel - \n\
В режиме тренировки для оценки памяти используется шкала:\n\
5 - perfect response\n\
4 - correct response after a hesitation\n\
3 - correct response recalled with serious difficulty\n\
2 - incorrect response; where the correct one seemed easy to recall\n\
1 - incorrect response; the correct one remembered\n\
0 - complete blackout.'
    )

@dp.message(Command(commands='list_all'), StateFilter(default_state, FSMmodel.add))
async def process_list_all_command(message: Message):
    # можно добавить проверку на наличие в кэше
    con, cur = db_open()
    cur.execute('SELECT object, meaning FROM bank WHERE user_id = %s ORDER BY object', (message.from_user.id,))
    response = cur.fetchall()
    db_close(con)
    res = list_all_data(response)
    await message.answer(res)

@dp.message(Command(commands='training'), StateFilter(default_state))
async def process_training_command(message: Message, state: FSMContext):
    con, cur = db_open()
    cur.execute('SELECT object, meaning, e_factor, interval, n \
FROM bank WHERE user_id = %s and next_date <= now()::DATE \
ORDER BY next_date - now()::DATE \
LIMIT %s', (message.from_user.id, Limit)
        )
    await state.update_data(objects = cur.fetchall())
    db_close(con)
    data = await state.get_data()
    objects = data["objects"]
    if objects:
        shuffle(objects)
        cur = 0
        await state.update_data(cur = cur, objects = objects)
        await message.answer(text=f'{objects[cur]["object"]}\n -------------------\n<tg-spoiler>{objects[cur]["meaning"]}</tg-spoiler>', \
                             reply_markup=builder.as_markup(), parse_mode='html')
        await state.set_state(FSMmodel.training)
    else:
        await message.answer(
            text='На сегодня нет объектов для тренировки, ты можешь попробовать повторить \
новые объекты или объекты, которые пока плохо запомнились:)'
        )

@dp.callback_query(StateFilter(FSMmodel.training), Response())
async def process_buttons_press(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    objects = data['objects']
    cur = int(data['cur'])
    objects[cur]['grade'] = callback.data
    print(cur, callback.data)
    cur += 1
    if cur < len(objects):
        await state.update_data(objects=objects)
        await state.update_data(cur = cur)
        await callback.message.edit_text(text=f'{objects[cur]["object"]}\n -------------------\n<tg-spoiler>{objects[cur]["meaning"]}</tg-spoiler>', \
                                         reply_markup=callback.message.reply_markup, parse_mode='html')
    else:
        await state.update_data(objects=objects)
        await update_db(state, callback.message.chat.id)
        await bot.send_message(chat_id=callback.from_user.id, text='Тренировка завершена. Данные обновлены.')
        await state.clear()


@dp.callback_query(StateFilter(FSMmodel.training), EndTraining())
async def process_end_training_press(callback: CallbackQuery, state: FSMContext):
    await update_db(state, callback.message.chat.id)
    await bot.send_message(
        chat_id=callback.message.chat.id, text='Тренировка остановлена. Данные обновлены.\n\
Вы можете продолжить позже повторно выбрав команду /training \n\
или перейти в режим изучения новых/проблемных объектов выбрав команду /learn'
    )
    await state.clear()


@dp.message(StateFilter(FSMmodel.training))
async def proces_text_press(message: Message):
    await message.answer(
            text='Вы находитесь в режиме тренировки, для завершения нажмите "End training" или выберите команду /cancel'
        )

@dp.message(Command(commands='learn'))
async def process_training_command(message: Message):
    con, cur = db_open()
    cur.execute('SELECT object, meaning \
FROM bank WHERE user_id = %s and n = 1 \
LIMIT %s', (message.chat.id, Limit)
        )
    learning_pool = cur.fetchall()
    db_close(con)
    if learning_pool:
        res = list_learning_pool(learning_pool)
        await message.answer(res, parse_mode='html')
    else:
        await message.answer('Сегодня учить нечего, для вывода полного списка слов нажимите /list_all')


@dp.message(Command(commands='add'), StateFilter(default_state))
async def process_add_command(message: Message, state: FSMContext):
    await message.answer(
        text='Вы в режиме добавление объекта в базу. \n\
Введите объект в формате: ключ = значение.\n\
Для выхода из режима ввода нажмите /cancel')
    await state.set_state(FSMmodel.add)

@dp.message(StateFilter(FSMmodel.add), Command(commands='cancel'))
async def process_exit_add_mode_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Вы вышли из режима ввода объекта.')

@dp.message(StateFilter(FSMmodel.add), Command(commands='add'))
async def process_add_in_progress_command(message: Message):
    await message.answer('Вы уже в режиме ввода.\n\
Введите объект в формате: ключ = значение.\n\
Для выхода из режима ввода нажмите /cancel')

@dp.message(StateFilter(FSMmodel.add), TextFilter())
async def process_new_entity_command(message: Message):
    await parse_add_value(message)

if __name__ == '__main__':
    dp.run_polling(bot)