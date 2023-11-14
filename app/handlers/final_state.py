from aiogram import Router
from aiogram.types import Message

from lexicon import LEXICON_RU
from models2.filters import TextFilter


router: Router = Router()


@router.message(TextFilter())
async def process_text_no_stat(message: Message):
    await message.answer(
            text=LEXICON_RU.get('final_state')
                )


@router.message()
async def process_any(message: Message):
    await message.answer(
            text='Я так не играю :(. Для вызова помошника нажмите /help.\n\
Для добавление объектов с использованием файла \
сначала перейдите в режим /add.')
