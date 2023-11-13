from datetime import datetime
from typing import Optional

from aiogram.fsm.context import FSMContext
from sqlalchemy import select, label, update, Result, insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.shemas import Category, Object

class DataService:

    def __init__(self, db: AsyncSession) -> None:

        self.db = db

    async def get_data(self, user_id: int, state: FSMContext) -> Optional[dict]:

        data: dict = await state.get_data()
        if not data:
            objects: list = await self.get_data_db(user_id, state)
            await state.update_data(
                deleted_objects=[], objects=objects,
                add_objects=[], training_data=[],
                categories=[], category=None)
        data: dict = await state.get_data()
        return data

    async def get_data_db(self, user_id: int, state: FSMContext) -> Optional[dict]:
        stmt = self._get_select_statement(user_id)
        result = await self.db.execute(stmt)
        data = self._prepare_data_for_serialisation(result)
        if data and len(data) > 0:
            await state.update_data(objects=data)
            return data

    async def update_db(self, user_id: int, state: FSMContext) -> None:
        res = await state.get_data()
        if res.get('training_data'): # and len(res["training_data"]) > 0:
            for ele in res['training_data']:
                grade = int(ele.get('grade', -1))
                e_factor = float(ele['e_factor'])
                n = int(ele['n'])
                interval = int(ele['interval'])
                if 0 <= grade < 3:
                    await self.db.execute(update(
                        {'id': ele.get('id'),
                         'next_date': datetime.utcnow().date() + 1,
                         'interval': 1.0,
                         'n': 1
                        }
                    ))
                elif grade >= 3:
                    e_factor = self._calc_e_factor(e_factor, grade)
                    interval = self._calc_interval(n, interval, e_factor)
                    await self.db.execute(update(
                        {'id': ele.get('id'),
                         'n': n+1,
                         'e_factor': e_factor,
                         'next_date': datetime.utcnow().date() + interval,
                         'interval': interval
                        }
                    ))
        if res['category']:
            stmt = self._get_select_statement_with_category(user_id, res['category'])
        else:
            stmt = self._get_select_statement(user_id)
        result = await self.db.execute(stmt)
        data = self._prepare_data_for_serialisation(result)
        await state.update_data(objects=data)

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

    def _calc_e_factor(self, prev_value: int, grade: int) -> float:
        return max(prev_value+(0.1-(5-grade)*(0.08+(5-grade)*0.02)), 1.3)

    def _calc_interval(n: int, prev_interval: int, e_factor: float) -> int:
        if n <= 1:
            return 1
        elif n == 2:
            return 6
        else:
            return round(prev_interval*e_factor)

    def _get_select_statement(self, user_id: int) -> str:
        stmt = select(Object.id, Object.object, Object.meaning, Object.e_factor,
                      Object.interval, Object.n, Object.category,
                      label('diff', Object.next_date - datetime.utcnow().date())).where(
                          Object.user_id == user_id).order_by(Object.object)
        return stmt

    def _get_select_statement_with_category(self, user_id: int,
                                            category: str) -> str:
        stmt = select(Object.id, Object.object, Object.meaning, Object.e_factor,
                      Object.interval, Object.n, Object.category,
                      label('diff', Object.next_date - datetime.utcnow().date())).where(
                          Object.user_id == user_id, Object.category == category).order_by(
                              Object.object)
        return stmt

    def _prepare_data_for_serialisation(self, result: list[Result]) -> list:
        data = [ele._asdict() for ele in result]
        for ele in data:
            ele['id'] = str(ele['id'])
        return data