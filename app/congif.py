from csv import reader
from json import loads
from random import choice

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BotCommand

from models import DbConnect, redis, Chat, CsvReadExeption


async def set_main_menu(bot: Bot):

    # Создаем список с командами и их описанием для кнопки menu
    main_menu_commands = [
        BotCommand(command='/list_all',
                   description='Вывод всех объектов'),
        BotCommand(command='/add',
                   description='Добавление объектов'),
        BotCommand(command='/delete',
                   description='Удаление объектов'),
        BotCommand(command='/training',
                   description='Режим тренировки'),
        BotCommand(command='/learn',
                   description='Режим изучения'),
        BotCommand(command='/help',
                   description='Справка по работе бота'),
        BotCommand(command='/cancel',
                   description='Для выхода из режима'),
            ]
    await bot.set_my_commands(main_menu_commands)


def _calc_e_factor(prev: int, g: int) -> float:
    return max(prev+(0.1-(5-g)*(0.08+(5-g)*0.02)), 1.3)


def _calc_interval(n: int, prev_interval: int, e_factor: float) -> int:
    if n <= 1:
        return 1
    elif n == 2:
        return 6
    else:
        return round(prev_interval*e_factor)


def list_all_data(lst: list) -> str:

    lst = sorted(lst, key=lambda x: x['object'])
    return '\n'.join(f"{i}. <b>{ele['object']}</b> = {ele['meaning']}."
                     if i == len(lst)
                     else f"{i}. <b>{ele['object']}</b> = {ele['meaning']};"
                     for i, ele in enumerate(lst, 1))


def list_learning_pool(lst: list) -> str:

    return '\n======================\n'.join(
        f"{i}. {choice((get_view_1, get_view_2))(ele, ' = ')}."
        if i == len(lst)
        else f"{i}. {choice((get_view_1, get_view_2))(ele, ' = ')};"
        for i, ele in enumerate(lst, 1))


def get_view_1(ele: dict, sep: str = "\n -------------------\n"):

    return f"{ele['object']}{sep}<tg-spoiler>{ele['meaning']}</tg-spoiler>"


def get_view_2(ele: dict, sep: str = "\n -------------------\n"):

    return f"{ele['meaning']}{sep}<tg-spoiler>{ele['object']}</tg-spoiler>"


def treat_object_list(lst: list) -> dict:

    if len(lst) > 0:
        return list(filter(lambda x: int(x['grade']) < 4, lst))
    else:
        return None


async def update_db(state: FSMContext, chat: str) -> None:

    res = await state.get_data()
    with DbConnect() as db:
        if res.get('training_data', False) and len(res["training_data"]) > 0:
            for ele in res['training_data']:
                grade = int(ele.get('grade', -1))
                e_factor = float(ele['e_factor'])
                n = ele['n']
                interval = int(ele['interval'])
                if 0 <= grade < 3:
                    db.cur.execute('UPDATE bank \
SET next_date = now()::DATE + 1, \
interval = DEFAULT, n = DEFAULT, modified = DEFAULT \
WHERE user_id = %s AND object = %s', (chat, ele["object"]))
                elif grade >= 3:
                    e_factor = _calc_e_factor(e_factor, grade)
                    interval = _calc_interval(n, interval, e_factor)
                    db.cur.execute(
                        'UPDATE bank SET n = %s, e_factor = %s, \
next_date = now()::DATE + %s, \
interval = %s, modified = DEFAULT WHERE user_id = %s AND object = %s',
                        (n+1, e_factor, interval,
                         interval, chat, ele["object"])
                    )
        db.cur.execute('SELECT object, meaning, e_factor, interval, n, \
(next_date - now()::DATE) as diff \
FROM bank WHERE user_id = %s ORDER BY object', (chat,))
        data = db.cur.fetchall()
        if data and len(data) > 0:
            await state.update_data(objects=data)


async def del_values_db(state: FSMContext, chat: str) -> None:

    res = await state.get_data()
    with DbConnect() as db:
        if res.get('deleted_objects', None) and res["deleted_objects"]:
            for ele in res["deleted_objects"]:
                db.cur.execute(
                    'DELETE FROM bank WHERE user_id = %s AND object = %s', (
                        chat, ele))
    await state.clear()


async def parse_add_value(message: Message) -> None:

    try:
        res = message.text.split('=')
        if len(res) != 2:
            raise ValueError('Значение некорректно. \
Введите объект в формате: ключ = значение.\n\
Для выхода из режима ввода нажмите /cancel')
        key = res[0].strip('\n .,').lower()
        value = res[1].strip('\n .,').lower()
        d = {'object': key, 'meaning': value, 'diff': 1}
        return d
    except ValueError as p:
        await message.answer(text=f'{p}')


async def add_values_db(state: FSMContext, chat: str) -> None:
    res = await state.get_data()
    with DbConnect() as db:
        if res.get('add_objects', None) and len(res["add_objects"]) > 0:
            db.cur.executemany('INSERT INTO bank (user_id, object, meaning) \
VALUES (%s, %s, %s) ON CONFLICT (user_id, object) DO NOTHING', (
                (chat, ele['object'],
                 ele['meaning']) for ele in res["add_objects"]))
    await state.clear()


async def get_data_db(chat: int, state: FSMContext) -> list:

    print('retriving data from DB')
    with DbConnect() as db:
        db.cur.execute('SELECT object, meaning, e_factor, interval, n, \
(next_date - now()::DATE) as diff \
FROM bank WHERE user_id = %s ORDER BY object', (chat,))
        data = db.cur.fetchall()
        if data and len(data) > 0:
            await state.update_data(objects=data)
            return data


async def get_data(state: FSMContext, chat: int):

    data: dict = await state.get_data()
    if not data:
        objects: list = await get_data_db(chat, state)
        await state.update_data(
            deleted_objects=[], objects=objects,
            add_objects=[], training_data=[])
        data: dict = await state.get_data()
    return data


async def update_values_db_auto(chat: Chat) -> None:
    res: str = await redis.get(f'fsm:{chat.id}:{chat.id}:data')
    if res:
        res: dict = loads(res)
        with DbConnect() as db:
            if res.get('add_objects', False) and len(res["add_objects"]) > 0:
                db.cur.executemany(
                    'INSERT INTO bank (user_id, object, meaning) \
VALUES (%s, %s, %s) ON CONFLICT (user_id, object) DO NOTHING', (
                        (chat.id, ele['object'], ele['meaning'])
                        for ele in res["add_objects"]))
            if res.get('deleted_objects', False):
                for ele in res["deleted_objects"]:
                    db.cur.execute(
                        'DELETE FROM bank WHERE user_id = %s AND object = %s',
                        (chat.id, ele))
            if res.get('training_data', False) \
                    and len(res["training_data"]) > 0:
                for ele in res['training_data']:
                    grade = int(ele.get('grade', -1))
                    e_factor = float(ele['e_factor'])
                    n = ele['n']
                    interval = int(ele['interval'])
                    if 0 <= grade < 3:
                        db.cur.execute(
                            'UPDATE bank SET next_date = now()::DATE + 1, \
interval = DEFAULT, n = DEFAULT, modified = DEFAULT \
WHERE user_id = %s AND object = %s', (chat.id, ele["object"]))
                    elif grade >= 3:
                        e_factor = _calc_e_factor(e_factor, grade)
                        interval = _calc_interval(n, interval, e_factor)
                        db.cur.execute(
                            'UPDATE bank SET n = %s, e_factor = %s, \
next_date = now()::DATE + %s, \
interval = %s, modified = DEFAULT WHERE user_id = %s AND object = %s', (
                                n+1, e_factor, interval,
                                interval, chat.id, ele["object"]))


async def check_status_auto(chat: Chat) -> bool:
    status: str = await redis.get(f'fsm:{chat.id}:{chat.id}:state')
    print(status)
    return status == 'FSMmodel:training'


def _strip_value(value: str):

    return value.strip('\n .,;:!').lower()


async def read_data_csv(file_name: str) -> list:

    with open(file_name, newline='') as f:
        try:
            data = reader(f, delimiter='=')
            cur = filter(lambda x: len(x) == 2, data)
            res = list(map(lambda x: [_strip_value(ele) for ele in x], cur))
            return res
        except:
            raise CsvReadExeption()


async def write_to_db_from_csv(chat: str, data: list) -> None:

    with DbConnect() as db:

        if data:
            db.cur.executemany('INSERT INTO bank (user_id, object, meaning) \
VALUES (%s, %s, %s) ON CONFLICT (user_id, object) DO NOTHING', (
                    (chat, *ele) for ele in data))


async def list_added_objects(lst: list) -> str:

    if lst:
        lst = sorted(lst)
        return '\n'.join(f"{i}. <b>{ele[0]}</b> = {ele[1]}."
            if i == len(lst) else f"{i}. <b>{ele[0]}</b> = {ele[1]};"
            for i, ele in enumerate(lst, 1))
