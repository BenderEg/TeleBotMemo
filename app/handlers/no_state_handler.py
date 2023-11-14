from aiogram import Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import Message

from core.dependencies import user_service
from lexicon import LEXICON_RU

router: Router = Router()

@router.message(CommandStart())
async def process_start_command(message: Message,
                                service: user_service):
    id=message.from_user.id,
    name=message.from_user.username
    await service.start(id, name)
    msg = f'Привет, {name}.\n'
    msg += LEXICON_RU['/start']
    await message.answer(text=msg)


@router.message(Command(commands='help'))
async def process_help_command(message: Message):
    await message.answer(text=LEXICON_RU['/help'])


@router.message(Command(commands='cancel'), StateFilter(default_state))
async def process_cancel_command(message: Message):
    await message.answer(text=LEXICON_RU['/cancel'])
