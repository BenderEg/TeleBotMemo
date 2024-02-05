from csv import reader

import backoff

from sqlalchemy import insert

from core.decorators import handle_db_errors
from db.postgres import db_session
from db.shemas import Object
from models.exeptions import CsvReadExeption, db_conn_exeptions
from services.base_service import BaseService

class CsvService(BaseService):

    def read_data_csv(self, file_name: str) -> list:
        with open(file_name, newline='') as f:
            try:
                data = reader(f, delimiter='=')
                cur = filter(lambda x: len(x) == 2, data)
                res = list(
                    map(lambda x: [self._strip_value(ele) for ele in x], cur)
                        )
                return res
            except:
                raise CsvReadExeption

    @handle_db_errors
    @backoff.on_exception(backoff.expo,
                          exception=db_conn_exeptions,
                          max_tries=5)
    async def add_data_to_db(self, data: list,
                             user_id: int, category: str) -> None:

        stmt = [{'user_id': user_id,
                 'object': ele[0],
                 'meaning': ele[1],
                 'category': category} for ele in data]
        await self.db.execute(insert(Object), stmt)
        await self.db.commit()

    def list_added_objects(self, data: list) -> str:

        if data:
            lst = sorted(data)
            return '\n'.join(f"{i}. <b>{ele[0]}</b> = {ele[1]}."
                         if i == len(lst) else f"{i}. <b>{ele[0]}</b> = \
                            {ele[1]};" for i, ele in enumerate(lst, 1))

    def _strip_value(self, value: str):
        return value.strip('\n .,;:!').lower()


async def get_csv_service(db: db_session) -> CsvService:
    return CsvService(db)