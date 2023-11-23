from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from core.config import settings
from db import redis_storage

bot: Bot | None = None
dp: Dispatcher | None = None

async def get_bot_instance():
    global bot, dp
    bot = Bot(settings.token)
    dp = Dispatcher(storage=RedisStorage(redis=await redis_storage.get_redis()))
    return bot, dp