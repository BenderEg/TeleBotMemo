import backoff

from db.shemas import User
from services.base_service import BaseService

from core.decorators import handle_db_errors
from core.logger import logging
from db.postgres import db_session
from models.exeptions import db_conn_exeptions

class UserService(BaseService):

    @handle_db_errors
    @backoff.on_exception(backoff.expo,
                          exception=db_conn_exeptions,
                          max_tries=5)
    async def start(self, id: int, name: str) -> None:
        user = await self.db.get(User, id)
        if user:
            user.name = name
        else:
            logging.info(f"Пользователь {name}/{id} присоединился к нам!")
            user = User(id=id, name=name)
            self.db.add(user)
        await self.db.commit()


async def get_user_service(db: db_session) -> UserService:
    return UserService(db)