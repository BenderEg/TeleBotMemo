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

def final_state(*args):
    logging.error(f'Failed to check schema creation: {args[0]}')


@backoff.on_exception(backoff.expo,
                      exception=(asyncpg.exceptions.ConnectionFailureError,
                                UnboundLocalError),
                      max_tries=7,
                      on_giveup=final_state)
async def main():
    try:
        con: asyncpg.Connection = await asyncpg.connect(**dsn)
        result = await con.fetchval(
            "select exists \
                (select * from pg_catalog.pg_namespace where nspname = $1)",
            settings.schema_db)
        return result
    except Exception as err:
        logging.error(f'Check schema creation error: {err}')
        raise asyncpg.exceptions.ConnectionFailureError
    finally:
        await con.close()

if __name__ == '__main__':
    asyncio.run(main())