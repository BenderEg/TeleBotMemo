from typing import Annotated

from aiogram3_di import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_session
from services.add_service import AddService
from services.category_service import CategoryService
from services.csv_service import CsvService
from services.del_service import DeleteService
from services.learning_service import LearningService
from services.user_service import UserService

db_session = Annotated[AsyncSession, Depends(get_session)]

async def get_user_service(db: db_session) -> UserService:
    return UserService(db)

async def get_category_service(db: db_session) -> CategoryService:
    return CategoryService(db)

async def get_add_service(db: db_session) -> AddService:
    return AddService(db)

async def get_delete_service(db: db_session) -> DeleteService:
    return DeleteService(db)

async def get_csv_service(db: db_session) -> CsvService:
    return CsvService(db)

async def get_learning_service(db: db_session) -> LearningService:
    return LearningService(db)

user_service = Annotated[UserService, Depends(get_user_service)]
category_service = Annotated[CategoryService, Depends(get_category_service)]
add_service = Annotated[AddService, Depends(get_add_service)]
del_service = Annotated[DeleteService, Depends(get_delete_service)]
csv_service = Annotated[CsvService, Depends(get_csv_service)]
learning_service = Annotated[LearningService, Depends(get_learning_service)]