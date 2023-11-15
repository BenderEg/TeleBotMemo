from uuid import UUID

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message
from pydantic import BaseModel, ValidationError


class UuidValidator(BaseModel):

    id: UUID

class TextFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.text:
            return {'text': message.text.strip('\n .,;:!')}
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

class Score(BaseFilter):

    async def __call__(self, callback: CallbackQuery) -> bool:
        if callback.data in ["0", "1", "2", "3", "4", "5"]:
            return {'score': callback.data}
        return False

class EndTraining(BaseFilter):

    async def __call__(self, callback: CallbackQuery) -> bool:
        if callback.data == '/cancel':
            return True
        return False

class CategoryResponse(BaseFilter):

    async def __call__(self, callback: CallbackQuery) -> bool:
        if callback.data:
            return {'text': callback.data}
        return False