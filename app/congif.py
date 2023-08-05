from pydantic import BaseModel
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from db_code import db_close, db_open
from aiogram.fsm.storage.redis import RedisStorage, Redis
from os import environ
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = environ["token"]
load_dotenv()

BOT_TOKEN = environ["token"]
redis: Redis = Redis(host=environ["host"])
storage: RedisStorage = RedisStorage(redis=redis)

Limit = 10

builder = InlineKeyboardBuilder()
for index in range(0, 6):
    builder.button(text=f"{index}", callback_data=f"{index}")
builder.button(text="End training", callback_data="/cancel")
builder.adjust(6,1)


class Response(BaseFilter):

    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.data in ["0", "1", "2", "3", "4", "5"]

class EndTraining(BaseFilter):

    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.data == '/cancel'



def calc_e_factor(prev: int, g: int) -> float:
    return max(prev+(0.1-(5-g)*(0.08+(5-g)*0.02)), 1.3)

def calc_interval(n: int, prev_interval: int, e_factor: float) -> int:
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
    con, cur = db_open()
    for ele in res['objects']:
        grade = int(ele['grade'])
        e_factor = int(ele['e_factor'])
        n = ele['n']
        interval = int(ele['interval'])
        if grade >= 0 and grade < 3:
            n = 1
            interval = calc_interval(n, interval, e_factor)
            cur.execute('UPDATE bank SET n = %s, e_factor = %s, next_date =  now()::DATE + %s, \
                        interval = %s WHERE user_id = %s', (1, e_factor, interval, interval, chat)
                )
        elif grade >= 3:
            e_factor = calc_e_factor(e_factor, n)
            interval = calc_interval(n, interval, e_factor)
            cur.execute('UPDATE bank SET n = %s, e_factor = %s, next_date =  now()::DATE + %s, \
                        interval = %s WHERE user_id = %s', (ele['n']+1, e_factor, interval, interval, chat)
                )
    db_close(con)
    await redis.delete(f'fsm:{chat}:{chat}:data')