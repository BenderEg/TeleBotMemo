from aiogram import Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message
from aiogram.fsm.state import default_state
from lexicon import LEXICON_RU
from models import DbConnect


router: Router = Router()


@router.message(CommandStart())
async def process_start_command(message: Message):
    with DbConnect() as db:
        db.cur.execute('INSERT INTO users (id) \
                       VALUES (%s) ON CONFLICT (id) DO NOTHING', (
            message.from_user.id,))
    await message.answer(text=LEXICON_RU['/start'])


@router.message(Command(commands='help'))
async def process_help_command(message: Message):
    await message.answer(text=LEXICON_RU['/help'])


@router.message(Command(commands='cancel'), StateFilter(default_state))
async def process_cancel_command(message: Message):
    await message.answer(
        text=LEXICON_RU['/cancel'])