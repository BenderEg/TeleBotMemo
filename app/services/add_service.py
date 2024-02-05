from db.postgres import db_session
from services.base_service import BaseService

class AddService(BaseService):

    def parse_add_value(self, text: str) -> dict:
        res = text.split('=')
        if len(res) != 2:
            raise ValueError
        key = res[0].strip('\n .,').lower()
        value = res[1].strip('\n .,').lower()
        d = {'object': key, 'meaning': value, 'diff': 1, 'n': 1}
        return d

async def get_add_service(db: db_session) -> AddService:
    return AddService(db)