from typing import Annotated

from aiogram3_di import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_session
from services.user_service import UserService
from services.category_service import CategoryService


db_session = Annotated[AsyncSession, Depends(get_session)]

async def get_user_service(db: db_session) -> UserService:
    return UserService(db)

async def get_category_service(db: db_session) -> CategoryService:
    return CategoryService(db)

user_service = Annotated[UserService, Depends(get_user_service)]
category_service = Annotated[CategoryService, Depends(get_category_service)]