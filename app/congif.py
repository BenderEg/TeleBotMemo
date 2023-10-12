from csv import reader
from json import loads
from random import choice
from typing import List

from sortedcontainers import SortedList

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BotCommand
from aiogram.utils.keyboard import InlineKeyboardBuilder

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
        BotCommand(command='/add_category',
                   description='Добавление категории для хранения объектов'),
        BotCommand(command='/choose_category',
                   description='Выбор категории'),
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


async def _group_by_categories(lst: list) -> dict:

    d = {}
    for ele in lst:
        if ele['category'] not in d:
            d[ele['category']] = SortedList([(ele['object'], ele['meaning'])])
        else:
            d[ele['category']].add((ele['object'], ele['meaning']))
    return d


async def list_all_data(lst: list) -> str:

    d = await _group_by_categories(lst)
    res = ''
    for key, value in d.items():
        header = f'<b>{key}:\n\n</b>'.upper()
        objects = '\n'.join(f"{i}. <b>{ele[0]}</b> = {ele[1]}."
                            if i == len(value)
                            else f"{i}. <b>{ele[0]}</b> = {ele[1]};"
                            for i, ele in enumerate(value, 1))
        res += header + objects + '\n\n'
    return res


async def list_learning_pool(lst: list) -> str:

    d = await _group_by_categories(lst)
    res = ''
    for key, value in d.items():
        header = f'<b>{key}:\n\n</b>'.upper()
        objects = '\n======================\n'.join(
            f"{i}. {choice((_get_view_internal_1, _get_view_internal_2))(ele, ' = ')}."
            if i == len(value)
            else f"{i}. {choice((_get_view_internal_1, _get_view_internal_2))(ele, ' = ')};"
            for i, ele in enumerate(value, 1))
        res += header + objects + '\n\n'
    return res


def _get_view_internal_1(ele: dict, sep: str = "\n -------------------\n"):

    return f"{ele[0]}{sep}<tg-spoiler>{ele[1]}</tg-spoiler>"


def _get_view_internal_2(ele: dict, sep: str = "\n -------------------\n"):

    return f"{ele[1]}{sep}<tg-spoiler>{ele[0]}</tg-spoiler>"


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
                                    interval = DEFAULT, \
                                    n = DEFAULT, \
                                    modified = DEFAULT \
                                    WHERE user_id = %s \
                                    AND object = %s \
                                    AND category = %s', (
                                        chat, ele["object"],
                                        ele['category']))
                elif grade >= 3:
                    e_factor = _calc_e_factor(e_factor, grade)
                    interval = _calc_interval(n, interval, e_factor)
                    db.cur.execute(
                        'UPDATE bank \
                         SET n = %s, e_factor = %s, \
                         next_date = now()::DATE + %s, \
                         interval = %s, \
                         modified = DEFAULT \
                         WHERE user_id = %s \
                         AND object = %s \
                         AND category = %s',
                        (n+1, e_factor, interval,
                         interval, chat, ele["object"],
                         ele['category'])
                    )
        if res['category']:
            db.cur.execute('SELECT object, meaning, e_factor, interval, n, \
                            (next_date - now()::DATE) as diff, \
                            category \
                            FROM bank \
                            WHERE user_id = %s \
                            AND category = %s \
                            ORDER BY object', (chat, res['category']))
        else:
            db.cur.execute('SELECT object, meaning, e_factor, interval, n, \
                            (next_date - now()::DATE) as diff, \
                            category \
                            FROM bank \
                            WHERE user_id = %s \
                            ORDER BY object', (chat, ))
        data = db.cur.fetchall()
        # if data and len(data) > 0:
        await state.update_data(objects=data)


async def del_values_db(state: FSMContext, chat: str) -> None:

    res = await state.get_data()
    with DbConnect() as db:
        if res.get('deleted_objects', False) and res["deleted_objects"]:
            for ele in res["deleted_objects"]:
                db.cur.execute(
                    'DELETE FROM bank \
                     WHERE user_id = %s \
                     AND object = %s \
                     AND category = %s', (
                        chat, ele[0], ele[1]))
    await state.update_data(deleted_objects=[])


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
            db.cur.executemany('INSERT INTO bank \
                               (user_id, object, meaning, category) \
                               VALUES (%s, %s, %s, %s) \
                               ON CONFLICT (user_id, object, category) \
                               DO NOTHING', (
                (chat, ele['object'],
                 ele['meaning'],
                 ele['category']) for ele in res["add_objects"])
                )


async def get_data_db(chat: int, state: FSMContext) -> list:

    print('retriving data from DB')
    with DbConnect() as db:
        db.cur.execute('SELECT object, meaning, e_factor, interval, n, \
                       (next_date - now()::DATE) as diff, \
                       category \
                       FROM bank \
                       WHERE user_id = %s \
                       ORDER BY object', (chat,))
        data = db.cur.fetchall()
        if data and len(data) > 0:
            await state.update_data(objects=data)
            return data


async def get_data(state: FSMContext, chat: int):

    data: dict = await state.get_data()
    if not data:
        objects: list = await get_data_db(chat, state)
        if not objects:
            objects = []
        await state.update_data(
            deleted_objects=[], objects=objects,
            add_objects=[], training_data=[],
            categories=[], category=None)
        data: dict = await state.get_data()
    return data


async def update_values_db_auto(chat: Chat) -> None:
    res: str = await redis.get(f'fsm:{chat.id}:{chat.id}:data')
    if res:
        res: dict = loads(res)
        with DbConnect() as db:
            if res.get('add_objects', False) and len(res["add_objects"]) > 0:
                db.cur.executemany(
                    'INSERT INTO bank (user_id, object, meaning, category) \
                        VALUES (%s, %s, %s, %s) \
                        ON CONFLICT (user_id, object, category) \
                        DO NOTHING', (
                        (chat.id, ele['object'],
                         ele['meaning'], ele['category'])
                        for ele in res["add_objects"]))
            if res.get('deleted_objects', False):
                for ele in res["deleted_objects"]:
                    db.cur.execute(
                        'DELETE FROM bank \
                         WHERE user_id = %s \
                         AND object = %s \
                         AND category = %s',
                        (chat.id, ele[0], ele[1]))
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
                             interval = DEFAULT, n = DEFAULT, \
                             modified = DEFAULT \
                             WHERE user_id = %s \
                             AND object = %s \
                             AND category = %s', (chat.id,
                                                  ele["object"],
                                                  ele["category"]))
                    elif grade >= 3:
                        e_factor = _calc_e_factor(e_factor, grade)
                        interval = _calc_interval(n, interval, e_factor)
                        db.cur.execute(
                            'UPDATE bank SET n = %s, e_factor = %s, \
                             next_date = now()::DATE + %s, \
                             interval = %s, \
                             modified = DEFAULT \
                             WHERE user_id = %s \
                             AND object = %s \
                             AND category = %s', (
                                n+1, e_factor, interval,
                                interval, chat.id,
                                ele["object"], ele["category"]))


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
            db.cur.executemany('INSERT INTO bank \
                               (user_id, object, meaning, category) \
                               VALUES (%s, %s, %s, %s) \
                               ON CONFLICT (user_id, object, category) \
                               DO NOTHING', (
                    (chat, *ele) for ele in data))


async def list_added_objects(lst: list) -> str:

    if lst:
        lst = sorted(lst)
        return '\n'.join(f"{i}. <b>{ele[0]}</b> = {ele[1]}."
                         if i == len(lst) else f"{i}. <b>{ele[0]}</b> = \
                            {ele[1]};" for i, ele in enumerate(lst, 1))


async def add_category_db(name: str, id: int, state: FSMContext) -> None:
    with DbConnect() as db:
        db.cur.execute('INSERT INTO categories (user_id, name) \
                       VALUES (%s, %s) \
                       ON CONFLICT (user_id, name) \
                       DO NOTHING', (id, name))
    await state.clear()


async def get_user_categories(message: Message):

    with DbConnect() as db:

        db.cur.execute('SELECT name \
                       FROM categories \
                       WHERE user_id=%s \
                       ORDER BY name',
                       (message.chat.id,))
        categories: list[dict] = db.cur.fetchall()
        if categories:
            categories = [ele.get('name') for ele in categories]
    return categories


async def create_categories_list(lst: List[dict]):
    builder = InlineKeyboardBuilder()
    for i, ele in enumerate(lst):
        builder.button(text=ele, callback_data=f"{i}")
    builder.button(text='Все категории', callback_data=f"{len(lst)}")
    builder.adjust(3, 1)
    return builder
