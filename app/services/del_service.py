from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import delete

from db.shemas import Object
from services.base_service import BaseService

class DeleteService(BaseService):

    async def del_values_db(self, user_id: int, state: FSMContext) -> None:
        res = await state.get_data()
        data = res.get('deleted_objects')
        if data:
            stmt = delete(Object).where(Object.id.in_(data))
            await self.db.execute(stmt)
            await self.db.commit()
        await state.update_data(deleted_objects=[])

    def create_delete_builder(
            self, objects: list) -> InlineKeyboardBuilder:
        builder = InlineKeyboardBuilder()
        for ele in objects:
            button_text = f"{ele['object']} = {ele['meaning']}"
            if len(button_text) > 30:
                button_text = f'{button_text[:30]}...'
            builder.button(text=button_text, callback_data=f"{ele['id']}")
        builder.adjust(1)
        return builder

    def filter_objects(self, objects: list, target_id: str) -> tuple:
        target_object = None
        filtered_objects = []
        for ele in objects:
            if ele['id'] == target_id:
                target_object = ele
            else:
                filtered_objects.append(ele)
        return target_object, filtered_objects