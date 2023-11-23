from json import loads

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from redis.asyncio import Redis
from sqlalchemy import select

from core.config import settings
from core.decorators import handle_db_errors
from core.dependencies import get_user_service
from db.postgres import get_session
from db.shemas import User
from services.user_service import UserService

scheduler = AsyncIOScheduler()

@handle_db_errors
async def get_users_list(service: UserService) -> list:

    query = select(User.id)
    result = await service.db.execute(query)
    users_id = result.scalars().partitions(100)
    return users_id

async def main():
    gen = get_session()
    db = await anext(gen)
    service: UserService = await get_user_service(db)
    async with Redis(host=settings.redis_host,
                     port=settings.redis_port,
                     db=settings.redis_db,
                     encoding="utf-8",
                     decode_responses=True) as redis:
        users_id = await get_users_list(service)
        for lst in users_id:
            for users_id in lst:
                key = f'fsm:{users_id}:{users_id}:data'
                data_json = await redis.get(key)
                if data_json:
                    data = loads(data_json)
                    await service.update_db(users_id, data)
                    await redis.delete(key)


scheduler.add_job(main, "interval", hours=settings.reset_frequency)
