from os import environ

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from congif import update_values_db_auto
from models import DbConnect, redis, Chat

scheduler = AsyncIOScheduler()


def get_users_list():

    with DbConnect() as db:

        db.cur.execute('SELECT id FROM users')
        while True:
            result = db.cur.fetchmany(100)
            if result:
                result = [Chat(**ele) for ele in result]
                yield result
            else:
                break


async def clear_cash():

    chat_list = get_users_list()
    for chats in chat_list:
        for chat in chats:
            await update_values_db_auto(chat)
            await redis.delete(f'fsm:{chat.id}:{chat.id}:data')

scheduler.add_job(clear_cash, "interval", hours=int(environ['RESET_HOURS']))
