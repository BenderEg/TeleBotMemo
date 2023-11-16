import asyncpg
import asyncio
import backoff

from core.config import settings
from core.logger import logging

dsn = {
    'host': settings.postgres_host,
    'port': settings.postgres_port,
    'database': settings.postgres_db,
    'user': settings.postgres_user,
    'password': settings.postgres_password
}

@backoff.on_predicate(backoff.expo, lambda x: x != True,
                      max_tries=7)
async def main():
    try:
        con: asyncpg.Connection = await asyncpg.connect(**dsn)
        result = await con.fetchval(
            "select exists \
                (select * from pg_catalog.pg_namespace where nspname = $1)",
            settings.schema)
        return result
    except Exception as err:
        logging.error(f'Check schema creation error: {err}')
    finally:
        await con.close()

if __name__ == '__main__':
    asyncio.run(main())