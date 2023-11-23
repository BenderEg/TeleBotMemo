from typing import Callable

from sqlalchemy.exc import IntegrityError

from core import bot
from core.config import settings
from core.logger import logging
from models.exeptions import ServerErrorExeption

def handle_db_errors(func: Callable) -> Callable:
    async def wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            return result
        except IntegrityError as err:
            raise IntegrityError(err.statement, err.params, err.orig)
        except Exception as err:
            logging.error(f'Database operation error: {err}')
            await bot.bot.send_message(
                chat_id=settings.owner,
                text='Database operation error.')
            raise ServerErrorExeption
    return wrapper
