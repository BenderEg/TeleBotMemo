from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from models import redis, DbConnect

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

def update_objects(object: dict, cur: dict, callback: CallbackQuery) -> dict:

    if object['object'] == cur['object']:
        object['grade'] = callback.data
    return object

async def update_db(state: FSMContext, chat: str) -> None:

    res = await state.get_data()
    with DbConnect() as db:
        for ele in res['objects']:
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
        await redis.delete(f'fsm:{chat}:{chat}:data')


async def parse_add_value(message: Message) -> None:

    with DbConnect() as db:
        try:
            res = message.text.split('=')
            if len(res) != 2:
                raise ValueError(
'Значение некорректно. Введите объект в формате: ключ = значение.\n\
Для выхода из режима ввода нажмите /cancel'
                )
            key, value = res[0].strip('\n .,').lower(), res[1].strip('\n .,').lower()
            db.cur.execute(
'INSERT INTO bank (user_id, object, meaning) VALUES (%s, %s, %s)', (message.from_user.id, key, value)
            )
            await message.answer(text='Объект добавлен в базу. Продолжайте ввод или нажмите /cancel для выхода из режима ввода')
        except ValueError as p:
            await message.answer(text=f'{p}')
        except:
            await message.answer(text=f'Проверьте, не содержит ли база значение ключа {key}. Повторите ввод.')