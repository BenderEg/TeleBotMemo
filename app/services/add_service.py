from aiogram.fsm.context import FSMContext
from sqlalchemy import insert

from db.shemas import Object
from services.base_service import BaseService

class AddService(BaseService):

    async def add_values_db(self, user_id: int, state: FSMContext) -> None:
        res = await state.get_data()
        data = res.get('add_objects')
        if data: # and len(res["add_objects"]) > 0:
            stmt = [{'user_id': user_id,
                     'object': ele['object'],
                     'meaning': ele['meaning'],
                     'category': ele['category']} for ele in data]
            await self.db.execute(insert(Object), stmt)
            await self.db.commit()

    def parse_add_value(self, text: str) -> dict:
        res = text.split('=')
        if len(res) != 2:
            raise ValueError
        key = res[0].strip('\n .,').lower()
        value = res[1].strip('\n .,').lower()
        d = {'object': key, 'meaning': value, 'diff': 1, 'n': 1}
        return d