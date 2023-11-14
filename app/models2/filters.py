from uuid import UUID

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message
from pydantic import BaseModel, ValidationError


class UuidValidator(BaseModel):

    id: UUID

class TextFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.text:
            return {'text': message.text}
        return False

class UuidFilter(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        try:
            _ = UuidValidator(id=callback.data)
            return {'value': callback.data}
        except ValidationError:
            return False

class FileFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.document:
            return {'name': message.document.file_name}
        return False
