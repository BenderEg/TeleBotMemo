from sqlalchemy.ext.asyncio import AsyncSession

from db.shemas import User

class UserService:

    def __init__(self, db: AsyncSession) -> None:

        self.db = db

    async def start(self, id: int, name: str) -> None:
        user = await self.db.get(User, id)
        if user:
            user.name = name
        else:
            user = User(id=id,
                        name=name)
            self.db.add(user)
        await self.db.commit()