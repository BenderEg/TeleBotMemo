from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from models import DbConnect


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
    return '\n'.join(f"{i}. {ele['object']} = {ele['meaning']}." \
                     if i == len(lst) else f"{i}. {ele['object']} = {ele['meaning']};" \
                        for i, ele in enumerate(lst, 1))


def list_learning_pool(lst: list) -> str:

    return '\n======================\n'.join(f"{i}. {ele['object']} = <tg-spoiler>{ele['meaning']}</tg-spoiler>." \
                     if i == len(lst) else f"{i}. {ele['object']} = <tg-spoiler>{ele['meaning']}</tg-spoiler>;" \
                        for i, ele in enumerate(lst, 1))


def treat_object_list(lst: list) -> dict:

    if len(lst) > 0:
        return list(filter(lambda x: int(x['grade']) < 4, lst))
    else:
        return None


# для чего эта функция?
def update_objects(object: dict, cur: dict, callback: CallbackQuery) -> dict:

    if object['object'] == cur['object']:
        object['grade'] = callback.data
    return object


async def update_db(state: FSMContext, chat: str) -> None:

    res = await state.get_data()
    with DbConnect() as db:
        for ele in res['training_data']:
            grade = int(ele.get('grade', -1))
            e_factor = float(ele['e_factor'])
            n = ele['n']
            interval = int(ele['interval'])
            if 0 <= grade < 3:
                db.cur.execute('UPDATE bank SET next_date = now()::DATE + 1, \
interval = DEFAULT, n = DEFAULT, modified = DEFAULT \
WHERE user_id = %s AND object = %s', (chat, ele["object"])
                )
            elif grade >= 3:
                e_factor = _calc_e_factor(e_factor, grade)
                interval = _calc_interval(n, interval, e_factor)
                db.cur.execute('UPDATE bank SET n = %s, e_factor = %s, next_date = now()::DATE + %s, \
interval = %s, modified = DEFAULT WHERE user_id = %s AND object = %s', (n+1, e_factor, interval, interval, chat, ele["object"])
                )
        db.cur.execute('SELECT object, meaning, e_factor, interval, n, (next_date - now()::DATE) as diff \
FROM bank WHERE user_id = %s ORDER BY object', (chat,)
            )
        data = db.cur.fetchall()
        if data and len(data) > 0:
            await state.update_data(objects = data)

async def del_values_db(state: FSMContext, chat: str) -> None:

    res = await state.get_data()
    with DbConnect() as db:
        for ele in res["deleted_objects"]:
            db.cur.execute('DELETE FROM bank WHERE user_id = %s AND object = %s', (chat, ele))
        # добавить обновление objects
        # await state.update_data(deleted_objects = [], filtered_objects = [])
        # await state.set_state(state=None)
    await state.clear()

async def parse_add_value(message: Message) -> None:

    try:
        res = message.text.split('=')
        if len(res) != 2:
            raise ValueError(
'Значение некорректно. Введите объект в формате: ключ = значение.\n\
Для выхода из режима ввода нажмите /cancel'
                )
        key, value = res[0].strip('\n .,').lower(), res[1].strip('\n .,').lower()
        d = {'object': key, 'meaning': value, 'diff': 1}
        return d
    except ValueError as p:
        await message.answer(text=f'{p}')


async def add_values_db(state: FSMContext, chat: str) -> None:
    res = await state.get_data()
    with DbConnect() as db:
        if len(res["add_objects"]) > 0:
            db.cur.executemany('INSERT INTO bank (user_id, object, meaning) \
VALUES (%s, %s, %s) ON CONFLICT (user_id, object) DO NOTHING', ((chat, ele['object'], ele['meaning']) for ele in res["add_objects"]))
            '''db.cur.execute('SELECT object, meaning, e_factor, interval, n, (next_date - now()::DATE) as diff \
FROM bank WHERE user_id = %s ORDER BY object', (chat,)
           )
            data = db.cur.fetchall()
            if data and len(data) > 0:
                await state.update_data(objects = data, add_objects = [])'''
    await state.clear()


async def get_data_db(chat: int, state: FSMContext) -> list:

    print('retriving data from DB')
    with DbConnect() as db:
        db.cur.execute('SELECT object, meaning, e_factor, interval, n, (next_date - now()::DATE) as diff \
FROM bank WHERE user_id = %s ORDER BY object', (chat,)
            )
        data = db.cur.fetchall()
        # print(f'data from DB {data}')
        if data and len(data) > 0:
            await state.update_data(objects = data)
            return data


async def get_data_cash(state: FSMContext) -> list:

    data = await state.get_data()
    if data.get('objects', False) and len(data['objects']) > 0:
        return data['objects']