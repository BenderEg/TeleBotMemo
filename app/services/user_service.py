from db.shemas import User
from services.base_service import BaseService

from core.decorators import handle_db_errors
from core.logger import logging

class UserService(BaseService):

    @handle_db_errors
    async def start(self, id: int, name: str) -> None:
        user = await self.db.get(User, id)
        if user:
            user.name = name
        else:
            logging.info(f"Пользователь {name}/{id} присоединился к нам!")
            user = User(id=id, name=name)
            self.db.add(user)
        await self.db.commit()
