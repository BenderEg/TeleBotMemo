from csv import reader
from json import loads
from random import choice
from typing import List

from sortedcontainers import SortedList


from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from models import DbConnect, redis, Chat


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
    return status == 'FSMmodel:training'
