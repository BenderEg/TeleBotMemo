from sqlalchemy.ext.asyncio import AsyncSession

from db.shemas import Category

class CategoryService:

    def __init__(self, db: AsyncSession) -> None:

        self.db = db

    async def add_category(self, user_id: int, name: str) -> None:
        category = Category(user_id=user_id, name=name)
        self.db.add(category)
        await self.db.commit()