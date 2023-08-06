from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.storage.redis import RedisStorage, Redis
from os import environ
from aiogram.filters.state import State, StatesGroup
import psycopg2
from psycopg2.extras import RealDictCursor
from time import sleep
from dotenv import load_dotenv

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

class FileFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.document.file_id:
            return {'name': message.document.file_name}
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

class Con:

    def __init__(self) -> None:

        self.con = psycopg2.connect(database=environ["POSTGRES_DB"],
                                   user=environ["POSTGRES_USER"],
                                   password=environ["POSTGRES_PASSWORD"],
                                   host=environ["HOST"],
                                   port=environ["PORT_DB"],
                                   cursor_factory=RealDictCursor)
        self.cur = self.con.cursor()

class DbConnect:

    def __init__(self) -> None:
        while True:
            try:
                self.db = Con()
                print('successuly connected')
                break
            except Exception as p:
                print('fail to connect to database')
                print(f'Error: {p}')
                sleep(1)

    def __enter__(self):
        return self.db

    def __exit__(self, *args):
        self.db.con.commit()
        self.db.con.close()
        return True