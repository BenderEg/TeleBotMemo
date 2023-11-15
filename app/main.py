import asyncio

from redis.asyncio import Redis

from core.bot import get_bot_instance
from core.menu import set_main_menu
from core.config import settings
from db import redis_storage
from handlers import no_state_handler, training, add_object, \
    learn, del_object, final_state, add_category, choose_category
from time_schedule import scheduler
from aiogram3_di import DIMiddleware

async def main() -> None:

    redis_storage.redis = Redis(host=settings.redis_host,
                                port=settings.redis_port,
                                db=settings.redis_db,
                                encoding="utf-8",
                                decode_responses=True)
    # Инициализируем бот и диспетчер

    bot, dp = await get_bot_instance()

    # Регистриуем роутеры в диспетчере
    dp.include_router(no_state_handler.router)
    dp.include_router(add_category.router)
    dp.include_router(choose_category.router)
    dp.include_router(learn.router)
    dp.include_router(training.router)
    dp.include_router(add_object.router)
    dp.include_router(del_object.router)
    dp.include_router(final_state.router)

    dp.message.middleware(DIMiddleware())
    dp.callback_query.middleware(DIMiddleware())

    # создаем меню
    await set_main_menu(bot)
    # Пропускаем накопившиеся апдейты и запускаем polling
    scheduler.start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
