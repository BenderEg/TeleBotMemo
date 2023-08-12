import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from congif import *
from models import *
from handlers import no_state_handler, training, add_object, learn, del_object, final_state
from time_schedule import scheduler

async def main() -> None:

    # Инициализируем бот и диспетчер
    bot: Bot = Bot(BOT_TOKEN)
    dp: Dispatcher = Dispatcher(storage=storage)

    # Регистриуем роутеры в диспетчере
    dp.include_router(no_state_handler.router)
    dp.include_router(learn.router)
    dp.include_router(training.router)
    dp.include_router(add_object.router)
    dp.include_router(del_object.router)
    dp.include_router(final_state.router)

    # Пропускаем накопившиеся апдейты и запускаем polling
    scheduler.start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
