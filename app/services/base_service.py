from datetime import datetime, timedelta
from typing import Optional

import backoff

from aiogram.fsm.context import FSMContext
from sqlalchemy import select, label, update, Result, delete, insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.decorators import handle_db_errors
from db.shemas import Object, User
from models.exeptions import db_conn_exeptions

class BaseService:

    def __init__(self, db: AsyncSession) -> None:

        self.db = db

    @handle_db_errors
    async def get_data(self, user_id: int, state: FSMContext) -> Optional[dict]:

        data: dict = await state.get_data()
        if not data:
            objects, categories = await self.get_data_db(user_id)
            await state.update_data(
                deleted_objects=[], objects=objects,
                add_objects=[], training_data=[],
                categories=categories, category=None)
            data: dict = await state.get_data()
        return data

    @backoff.on_exception(backoff.expo,
                          exception=db_conn_exeptions,
                          max_tries=5)
    async def get_data_db(self, user_id: int) -> Optional[dict]:
        stmt = self._get_select_statement(user_id)
        result = await self.db.execute(stmt)
        objects = self._prepare_data_for_serialisation(result)
        categories = await self.get_user_categories(user_id)
        return objects, categories

    @handle_db_errors
    async def update_db(self, user_id: int, data: dict) -> tuple:
        if data.get('training_data'):
            await self.update_training_data(data.get('training_data'))
        if data.get('deleted_objects'):
            await self.del_values_db(data.get('deleted_objects'))
        if data.get('add_objects'):
            await self.add_values_db(user_id, data.get('add_objects'))
        await self.db.commit()
        if data['category']:
            query = self._get_select_statement_with_category(user_id, data['category'])
        else:
            query = self._get_select_statement(user_id)
        result = await self.db.execute(query)
        objects = self._prepare_data_for_serialisation(result)
        categories = await self.get_user_categories(user_id)
        return objects, categories

    async def update_state(self, objects: list,
                           categories: list, state: FSMContext) -> None:
        await state.update_data(objects=objects,
                                categories=categories,
                                add_objects=[],
                                training_data=[],
                                deleted_objects=[])

    def _calc_e_factor(self, prev_value: int, grade: int) -> float:
        return max(prev_value+(0.1-(5-grade)*(0.08+(5-grade)*0.02)), 1.3)

    def _calc_interval(self, n: int, prev_interval: int, e_factor: float) -> int:
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

    @backoff.on_exception(backoff.expo,
                          exception=db_conn_exeptions,
                          max_tries=5)
    async def update_training_data(self, data: list) -> None:
        stmt = []
        for ele in data:
            grade = int(ele.get('grade', -1))
            e_factor = float(ele['e_factor'])
            n = int(ele['n'])
            interval = int(ele['interval'])
            if 0 <= grade < 3:
                stmt.append(
                    {'id': ele.get('id'),
                     'n': 1,
                     'e_factor': e_factor,
                     'next_date': datetime.utcnow().date() + timedelta(1),
                     'interval': 1.0
                    })
            elif grade >= 3:
                e_factor = self._calc_e_factor(e_factor, grade)
                interval = self._calc_interval(n, interval, e_factor)
                stmt.append(
                    {'id': ele.get('id'),
                     'n': n+1,
                     'e_factor': e_factor,
                     'next_date': datetime.utcnow().date() + timedelta(interval),
                     'interval': interval
                    })
        await self.db.execute(update(Object), stmt)

    @backoff.on_exception(backoff.expo,
                          exception=db_conn_exeptions,
                          max_tries=5)
    async def del_values_db(self, data: list) -> None:
        if data:
            stmt = delete(Object).where(Object.id.in_(data))
            await self.db.execute(stmt)

    @backoff.on_exception(backoff.expo,
                          exception=db_conn_exeptions,
                          max_tries=5)
    async def add_values_db(self, user_id: int, data: list) -> None:
        stmt = [{'user_id': user_id,
                 'object': ele['object'],
                 'meaning': ele['meaning'],
                 'category': ele['category']} for ele in data]
        await self.db.execute(insert(Object), stmt)

    @backoff.on_exception(backoff.expo,
                          exception=db_conn_exeptions,
                          max_tries=5)
    async def get_user_categories(self, user_id: int) -> list:
        user = await self.db.get(User, user_id)
        if user and user.categories:
            categories = [ele.name for ele in user.categories]
            return categories
