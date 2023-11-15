from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.decorators import handle_db_errors
from db.shemas import Category
from services.base_service import BaseService

class CategoryService(BaseService):

    @handle_db_errors
    async def add_category(self, user_id: int, name: str) -> None:
        category = Category(user_id=user_id, name=name)
        self.db.add(category)
        await self.db.commit()

    def create_categories_list(self,
                               categories: list) -> InlineKeyboardBuilder:
        builder = InlineKeyboardBuilder()
        for ele in categories:
            builder.button(text=ele, callback_data=ele)
        builder.button(text='Все категории',
                       callback_data='Все категории')
        builder.adjust(3, 1)
        return builder
