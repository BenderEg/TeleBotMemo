from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from db.shemas import Category, User

class CategoryService:

    def __init__(self, db: AsyncSession) -> None:

        self.db = db

    async def add_category(self, user_id: int, name: str) -> None:
        category = Category(user_id=user_id, name=name)
        self.db.add(category)
        await self.db.commit()

    async def get_user_categories(self, user_id) -> list:
        user = await self.db.get(User, user_id)
        if user and user.categories:
            categories = [ele.name for ele in user.categories]
            return categories

    def create_categories_list(self,
                               categories: list) -> InlineKeyboardBuilder:
        builder = InlineKeyboardBuilder()
        for i, ele in enumerate(categories):
            builder.button(text=ele, callback_data=f"{i}")
        builder.button(text='Все категории',
                           callback_data=f"{len(categories)}")
        builder.adjust(3, 1)
        return builder
