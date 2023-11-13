from typing import Annotated

from aiogram3_di import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_session
from services.category_service import CategoryService
from services.csv_service import CsvService
from services.data_service import DataService
from services.user_service import UserService

db_session = Annotated[AsyncSession, Depends(get_session)]

async def get_user_service(db: db_session) -> UserService:
    return UserService(db)

async def get_category_service(db: db_session) -> CategoryService:
    return CategoryService(db)

async def get_data_service(db: db_session) -> DataService:
    return DataService(db)

async def get_csv_service(db: db_session) -> CsvService:
    return CsvService(db)

user_service = Annotated[UserService, Depends(get_user_service)]
category_service = Annotated[CategoryService, Depends(get_category_service)]
data_service = Annotated[DataService, Depends(get_data_service)]
csv_service = Annotated[CsvService, Depends(get_csv_service)]