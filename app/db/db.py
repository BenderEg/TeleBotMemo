from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from core.config import settings


Base = declarative_base(metadata=MetaData(schema="memo"))

dsn = f'''postgresql+asyncpg://{
    settings.postgres_user}:{settings.postgres_password}@{
        settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}'''
engine = create_async_engine(dsn, echo=settings.echo, future=True)
async_session = sessionmaker(engine, class_=AsyncSession,
                             expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

'''
async def create_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
'''