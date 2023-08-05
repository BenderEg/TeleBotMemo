from pydantic import BaseModel
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.storage.redis import RedisStorage, Redis
from os import environ
from dotenv import load_dotenv
from aiogram.filters.state import State, StatesGroup


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

class TextFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.text:
            return {'text': message.text}
        return False

class EndTraining(BaseFilter):

    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.data == '/cancel'

class FSMmodel(StatesGroup):
    # Создаем экземпляры класса State, последовательно
    # перечисляя возможные состояния, в которых будет находиться
    # бот в разные моменты взаимодейтсвия с пользователем
    training = State()        # Состояние тренировки
    add = State() # Состояние изучения объектов