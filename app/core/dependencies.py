from typing import Annotated

from aiogram3_di import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_session
from services.user_service import UserService


db_session = Annotated[AsyncSession, Depends(get_session)]

async def get_user_service(db: db_session) -> UserService:
    return UserService(db)

user_service = Annotated[UserService, Depends(get_user_service)]